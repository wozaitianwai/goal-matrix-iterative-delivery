import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import goalMatrixExtension, { previewWebhook, sendWebhook } from "../index.js";

function createHarness() {
  const events = new Map();
  const commands = new Map();
  const sentUserMessages = [];
  const pi = {
    on(eventName, handler) {
      events.set(eventName, handler);
    },
    registerCommand(name, options) {
      commands.set(name, options);
    },
    sendUserMessage(text, options) {
      sentUserMessages.push({ text, options });
    },
  };
  goalMatrixExtension(pi);
  return { events, commands, sentUserMessages };
}

function tempProject(config, localConfig) {
  const root = mkdtempSync(join(tmpdir(), "goal-matrix-notify-"));
  mkdirSync(join(root, ".goal-matrix"), { recursive: true });
  writeFileSync(join(root, ".goal-matrix", "notifications.json"), JSON.stringify(config, null, 2));
  if (localConfig) {
    writeFileSync(join(root, ".goal-matrix", "notifications.local.json"), JSON.stringify(localConfig, null, 2));
  }
  return root;
}

function notifyContext(root, notifications) {
  return {
    cwd: root,
    ui: {
      notify(message, level) {
        notifications.push({ message, level });
      },
    },
  };
}

test("registers goal notification command", () => {
  const { commands } = createHarness();

  assert.ok(commands.has("goal-notify"));
});

test("/goal-notify test uses Codex popup notify instead of chat", async () => {
  const root = tempProject({ enabled: true, codexPopup: { enabled: true } });
  const notifications = [];
  const { commands, sentUserMessages } = createHarness();

  try {
    await commands.get("goal-notify").handler("test", notifyContext(root, notifications));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(sentUserMessages.length, 0);
  assert.equal(notifications.length, 1);
  assert.match(notifications[0].message, /Goal Matrix notification test/);
});

test("session_start shows popup only when project notification config is enabled", async () => {
  const root = tempProject({
    enabled: true,
    codexPopup: { enabled: true, events: ["session_start"] },
  });
  const notifications = [];
  const { events } = createHarness();

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, notifications));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(notifications.length, 1);
  assert.match(notifications[0].message, /Goal Matrix notifications enabled/);
});

test("disabled project notification config stays silent", async () => {
  const root = tempProject({ enabled: false, codexPopup: { enabled: true } });
  const notifications = [];
  const { events } = createHarness();

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, notifications));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }

  assert.deepEqual(notifications, []);
});

test("tracked project config cannot enable webhook egress", async () => {
  const root = tempProject({
    enabled: true,
    codexPopup: { enabled: false },
    webhook: {
      enabled: true,
      events: ["session_start"],
      url: "https://example.invalid/tracked-webhook",
    },
  });
  const originalFetch = globalThis.fetch;
  let fetchCalled = false;
  const { events } = createHarness();
  globalThis.fetch = async () => {
    fetchCalled = true;
    return { ok: true, status: 200 };
  };

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, []));
  } finally {
    globalThis.fetch = originalFetch;
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(fetchCalled, false);
});

test("tracked project config cannot select a webhook URL environment variable", async () => {
  const root = tempProject({
    enabled: true,
    codexPopup: { enabled: false },
    webhook: {
      enabled: true,
      events: ["session_start"],
      urlEnv: "GOAL_MATRIX_UNRELATED_URL",
    },
  });
  const originalUrl = process.env.GOAL_MATRIX_UNRELATED_URL;
  const originalFetch = globalThis.fetch;
  let fetchCalled = false;
  const { events } = createHarness();
  process.env.GOAL_MATRIX_UNRELATED_URL = "https://example.invalid/unrelated";
  globalThis.fetch = async () => {
    fetchCalled = true;
    return { ok: true, status: 200 };
  };

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, []));
  } finally {
    if (originalUrl === undefined) delete process.env.GOAL_MATRIX_UNRELATED_URL;
    else process.env.GOAL_MATRIX_UNRELATED_URL = originalUrl;
    globalThis.fetch = originalFetch;
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(fetchCalled, false);
});

test("local notification config can explicitly enable webhook egress", async () => {
  const root = tempProject(
    {
      enabled: true,
      codexPopup: { enabled: false },
      webhook: { events: ["session_start"] },
    },
    {
      webhook: {
        enabled: true,
        url: "https://example.invalid/local-webhook",
      },
    },
  );
  const originalFetch = globalThis.fetch;
  const fetchCalls = [];
  const { events } = createHarness();
  globalThis.fetch = async (url) => {
    fetchCalls.push(url);
    return { ok: true, status: 200 };
  };

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, []));
  } finally {
    globalThis.fetch = originalFetch;
    rmSync(root, { recursive: true, force: true });
  }

  assert.deepEqual(fetchCalls, ["https://example.invalid/local-webhook"]);
});

test("enabled webhook notification sends provider payload without chat", async () => {
  const root = tempProject({
    enabled: true,
    codexPopup: { enabled: false },
    webhook: {
      enabled: true,
      events: ["session_start"],
      provider: "discord",
      presets: {
        discord: {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: {
            content: "{{message}}",
            event: "{{event}}",
          },
        },
      },
    },
  });
  const originalUrl = process.env.GOAL_MATRIX_WEBHOOK_URL;
  const originalFetch = globalThis.fetch;
  const fetchCalls = [];
  const notifications = [];
  const { events, sentUserMessages } = createHarness();

  process.env.GOAL_MATRIX_WEBHOOK_URL = "https://example.invalid/webhook";
  globalThis.fetch = async (url, options) => {
    fetchCalls.push({ url, options });
    return { ok: true, status: 200 };
  };

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, notifications));
  } finally {
    if (originalUrl === undefined) {
      delete process.env.GOAL_MATRIX_WEBHOOK_URL;
    } else {
      process.env.GOAL_MATRIX_WEBHOOK_URL = originalUrl;
    }
    globalThis.fetch = originalFetch;
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(sentUserMessages.length, 0);
  assert.deepEqual(notifications, []);
  assert.equal(fetchCalls.length, 1);
  assert.equal(fetchCalls[0].url, "https://example.invalid/webhook");
  assert.equal(fetchCalls[0].options.method, "POST");
  assert.ok(fetchCalls[0].options.signal);
  assert.deepEqual(JSON.parse(fetchCalls[0].options.body), {
    content: "Goal Matrix notifications enabled for this project.",
    event: "session_start",
  });
});

test("webhook rejects non-https URLs before fetch", async () => {
  const originalFetch = globalThis.fetch;
  let fetchCalled = false;
  globalThis.fetch = async () => {
    fetchCalled = true;
    return { ok: true, status: 200 };
  };

  try {
    const sent = await sendWebhook(
      {
        enabled: true,
        webhook: { enabled: true, events: ["session_start"], url: "http://example.invalid/webhook" },
      },
      "session_start",
      "message",
    );

    assert.equal(sent, false);
    assert.equal(fetchCalled, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("webhook enforces allowed host list", async () => {
  const originalFetch = globalThis.fetch;
  let fetchCalled = false;
  globalThis.fetch = async () => {
    fetchCalled = true;
    return { ok: true, status: 200 };
  };

  try {
    const sent = await sendWebhook(
      {
        enabled: true,
        webhook: {
          enabled: true,
          events: ["session_start"],
          url: "https://evil.invalid/webhook",
          allowedHosts: ["example.invalid"],
        },
      },
      "session_start",
      "message",
    );

    assert.equal(sent, false);
    assert.equal(fetchCalled, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("webhook reports non-ok responses as failed", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (_url, options) => {
    assert.ok(options.signal);
    return { ok: false, status: 500 };
  };

  try {
    const sent = await sendWebhook(
      {
        enabled: true,
        webhook: { enabled: true, events: ["session_start"], url: "https://example.invalid/webhook" },
      },
      "session_start",
      "message",
    );

    assert.equal(sent, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("webhook preview is dry-run and uses whitelisted event fields", () => {
  const preview = previewWebhook(
    {
      enabled: true,
      webhook: {
        enabled: true,
        events: ["session_start"],
        provider: "generic",
        url: "https://example.invalid/webhook?token=secret",
        eventFields: ["event", "provider"],
        presets: {
          generic: {
            method: "POST",
            headers: { "X-Event": "{{event}}", "X-Message": "{{message}}" },
            body: { event: "{{event}}", provider: "{{provider}}", message: "{{message}}", secret: "{{secret}}" },
          },
        },
      },
    },
    "session_start",
    "message",
  );

  assert.equal(preview.dryRun, true);
  assert.equal(preview.url, "https://example.invalid/webhook?redacted=1");
  assert.deepEqual(preview.headers, { "X-Event": "session_start", "X-Message": "" });
  assert.deepEqual(preview.body, { event: "session_start", provider: "generic", message: "", secret: "" });
});

test("/goal-notify webhook-dry-run previews without fetch", async () => {
  const root = tempProject({
    enabled: true,
    webhook: {
      enabled: true,
      events: ["session_start"],
      url: "https://example.invalid/webhook",
      presets: { generic: { body: { text: "{{message}}" } } },
    },
  });
  const originalFetch = globalThis.fetch;
  let fetchCalled = false;
  const notifications = [];
  const { commands } = createHarness();
  globalThis.fetch = async () => {
    fetchCalled = true;
    return { ok: true, status: 200 };
  };

  try {
    await commands.get("goal-notify").handler("webhook-dry-run", notifyContext(root, notifications));
  } finally {
    globalThis.fetch = originalFetch;
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(fetchCalled, false);
  assert.equal(notifications.length, 1);
  assert.match(notifications[0].message, /webhook dry-run/);
  assert.match(notifications[0].message, /session_start/);
});
