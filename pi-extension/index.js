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
  return mergeConfig(
    mergeConfig(DEFAULT_CONFIG, readJson(join(configDir, "notifications.json"))),
    readJson(join(configDir, "notifications.local.json")),
  );
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

async function sendWebhook(config, eventName, message) {
  if (!webhookEventEnabled(config, eventName)) return false;
  const url = webhookUrl(config);
  if (!url || typeof globalThis.fetch !== "function") return false;

  const provider = config.webhook?.provider || "generic";
  const preset = config.webhook?.presets?.[provider] || config.webhook?.presets?.generic || {};
  const variables = { event: eventName, message, provider };
  const body = templateValue(preset.body || { text: "{{message}}" }, variables);

  try {
    await globalThis.fetch(url, {
      method: preset.method || "POST",
      headers: templateValue(preset.headers || { "Content-Type": "application/json" }, variables),
      body: JSON.stringify(body),
    });
    return true;
  } catch {
    return false;
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
