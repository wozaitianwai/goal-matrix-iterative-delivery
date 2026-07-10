import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const DEFAULT_CONFIG = {
  enabled: false,
  codexPopup: {
    enabled: true,
    events: ["session_start", "agent_end"],
  },
  webhook: {
    enabled: false,
    events: ["session_start", "agent_end"],
    provider: "generic",
    urlEnv: "GOAL_MATRIX_WEBHOOK_URL",
    eventFields: ["event", "message", "provider"],
    presets: {},
  },
};

function isObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function mergeConfig(base, override) {
  const merged = { ...base };
  if (!isObject(override)) return merged;

  for (const [key, value] of Object.entries(override)) {
    merged[key] = isObject(value) && isObject(merged[key])
      ? mergeConfig(merged[key], value)
      : value;
  }
  return merged;
}

function readJson(path) {
  if (!existsSync(path)) return {};
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return {};
  }
}

export function projectRoot(ctx) {
  return resolve(ctx?.cwd || ctx?.workspace?.root || process.cwd());
}

export function readNotificationConfig(root) {
  const configDir = join(root, ".goal-matrix");
  const tracked = readJson(join(configDir, "notifications.json"));
  const local = readJson(join(configDir, "notifications.local.json"));
  const config = mergeConfig(mergeConfig(DEFAULT_CONFIG, tracked), local);
  const localWebhook = isObject(local.webhook) ? local.webhook : {};
  const url = typeof localWebhook.url === "string" ? localWebhook.url : "";
  const urlEnv = typeof localWebhook.urlEnv === "string" && localWebhook.urlEnv
    ? localWebhook.urlEnv
    : DEFAULT_CONFIG.webhook.urlEnv;
  const envUrl = urlEnv ? process.env[urlEnv] : "";

  config.webhook = {
    ...config.webhook,
    enabled: localWebhook.enabled === false
      ? false
      : localWebhook.enabled === true || Boolean(url || envUrl),
    url,
    urlEnv,
  };
  return config;
}

function popupEventEnabled(config, eventName) {
  if (!config.enabled || config.codexPopup?.enabled === false) return false;
  const events = Array.isArray(config.codexPopup?.events) ? config.codexPopup.events : DEFAULT_CONFIG.codexPopup.events;
  return events.includes(eventName);
}

function providerNames(config) {
  return Object.keys(config.webhook?.presets || {}).sort();
}

function notify(ctx, message, level = "info") {
  ctx?.ui?.notify?.(message, level);
}

function templateValue(value, variables) {
  if (typeof value === "string") {
    return value.replace(/\{\{([a-zA-Z0-9_]+)\}\}/g, (_match, name) => String(variables[name] ?? ""));
  }
  if (Array.isArray(value)) return value.map((item) => templateValue(item, variables));
  if (isObject(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, templateValue(item, variables)]));
  }
  return value;
}

function webhookEventEnabled(config, eventName) {
  if (!config.enabled || config.webhook?.enabled !== true) return false;
  const events = Array.isArray(config.webhook?.events) ? config.webhook.events : DEFAULT_CONFIG.webhook.events;
  return events.includes(eventName);
}

function webhookUrl(config) {
  const envName = config.webhook?.urlEnv || DEFAULT_CONFIG.webhook.urlEnv;
  return config.webhook?.url || (envName ? process.env[envName] : "");
}

function safeWebhookUrl(config) {
  const rawUrl = webhookUrl(config);
  if (!rawUrl) return null;
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    return null;
  }
  if (parsed.protocol !== "https:") return null;
  const allowedHosts = Array.isArray(config.webhook?.allowedHosts) ? config.webhook.allowedHosts : [];
  if (allowedHosts.length && !allowedHosts.includes(parsed.hostname)) return null;
  return parsed.toString();
}

function redactedWebhookUrl(url) {
  if (!url) return null;
  const parsed = new URL(url);
  parsed.username = "";
  parsed.password = "";
  parsed.search = parsed.search ? "?redacted=1" : "";
  return parsed.toString();
}

function webhookVariables(config, eventName, message, provider) {
  const allowed = Array.isArray(config.webhook?.eventFields)
    ? config.webhook.eventFields
    : DEFAULT_CONFIG.webhook.eventFields;
  const source = { event: eventName, message, provider };
  return Object.fromEntries(allowed.filter((field) => field in source).map((field) => [field, source[field]]));
}

function webhookRequest(config, eventName, message) {
  if (!webhookEventEnabled(config, eventName)) return false;
  const url = safeWebhookUrl(config);
  if (!url || typeof globalThis.fetch !== "function") return false;

  const provider = config.webhook?.provider || "generic";
  const preset = config.webhook?.presets?.[provider] || config.webhook?.presets?.generic || {};
  const variables = webhookVariables(config, eventName, message, provider);
  const body = templateValue(preset.body || { text: "{{message}}" }, variables);
  const timeoutMs = Number.isFinite(config.webhook?.timeoutMs) ? config.webhook.timeoutMs : 5000;
  return {
    url,
    event: eventName,
    provider,
    method: preset.method || "POST",
    headers: templateValue(preset.headers || { "Content-Type": "application/json" }, variables),
    body,
    timeoutMs,
  };
}

export function previewWebhook(config, eventName, message) {
  const request = webhookRequest(config, eventName, message);
  if (!request) {
    return { dryRun: true, enabled: false, event: eventName };
  }
  return {
    dryRun: true,
    enabled: true,
    event: request.event,
    provider: request.provider,
    url: redactedWebhookUrl(request.url),
    method: request.method,
    headers: request.headers,
    body: request.body,
  };
}

export async function sendWebhook(config, eventName, message) {
  const request = webhookRequest(config, eventName, message);
  if (!request) return false;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), request.timeoutMs);

  try {
    const response = await globalThis.fetch(request.url, {
      method: request.method,
      headers: request.headers,
      body: JSON.stringify(request.body),
      signal: controller.signal,
    });
    return Boolean(response?.ok);
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

async function notifyForEvent(eventName, ctx, message) {
  const config = readNotificationConfig(projectRoot(ctx));
  if (popupEventEnabled(config, eventName)) notify(ctx, message, "info");
  await sendWebhook(config, eventName, message);
}

export default function goalMatrixExtension(pi) {
  pi.registerCommand("goal-notify", {
    description: "Show Goal Matrix project notification status",
    handler: async (args, ctx) => {
      const command = String(args || "status").trim().toLowerCase() || "status";
      const config = readNotificationConfig(projectRoot(ctx));

      if (command === "test") {
        notify(ctx, "Goal Matrix notification test.", "info");
        return;
      }

      if (command === "templates") {
        notify(ctx, `Goal Matrix webhook presets: ${providerNames(config).join(", ") || "none"}.`, "info");
        return;
      }

      if (command === "webhook-dry-run" || command === "dry-run" || command === "preview") {
        const preview = previewWebhook(config, "session_start", "Goal Matrix webhook dry-run.");
        notify(ctx, `Goal Matrix webhook dry-run: ${JSON.stringify(preview)}`, "info");
        return;
      }

      notify(
        ctx,
        `Goal Matrix notifications ${config.enabled ? "enabled" : "disabled"}; popup ${config.codexPopup?.enabled === false ? "off" : "on"}; webhook provider ${config.webhook?.provider || "generic"}.`,
        config.enabled ? "info" : "warning",
      );
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    await notifyForEvent("session_start", ctx, "Goal Matrix notifications enabled for this project.");
  });

  pi.on("agent_end", async (_event, ctx) => {
    await notifyForEvent("agent_end", ctx, "Goal Matrix agent run ended. Verify and checkpoint before completion.");
  });
}
