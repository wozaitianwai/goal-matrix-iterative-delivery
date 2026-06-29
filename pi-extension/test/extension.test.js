import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import goalMatrixExtension from "../index.js";

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

function tempProject(config) {
  const root = mkdtempSync(join(tmpdir(), "goal-matrix-notify-"));
  mkdirSync(join(root, ".goal-matrix"), { recursive: true });
  writeFileSync(join(root, ".goal-matrix", "notifications.json"), JSON.stringify(config, null, 2));
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

test("enabled webhook notification sends provider payload without chat", async () => {
  const root = tempProject({
    enabled: true,
    codexPopup: { enabled: false },
    webhook: {
      enabled: true,
      events: ["session_start"],
      provider: "discord",
      urlEnv: "GOAL_MATRIX_TEST_WEBHOOK_URL",
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
  const originalUrl = process.env.GOAL_MATRIX_TEST_WEBHOOK_URL;
  const originalFetch = globalThis.fetch;
  const fetchCalls = [];
  const notifications = [];
  const { events, sentUserMessages } = createHarness();

  process.env.GOAL_MATRIX_TEST_WEBHOOK_URL = "https://example.invalid/webhook";
  globalThis.fetch = async (url, options) => {
    fetchCalls.push({ url, options });
    return { ok: true, status: 200 };
  };

  try {
    await events.get("session_start")({ reason: "startup" }, notifyContext(root, notifications));
  } finally {
    if (originalUrl === undefined) {
      delete process.env.GOAL_MATRIX_TEST_WEBHOOK_URL;
    } else {
      process.env.GOAL_MATRIX_TEST_WEBHOOK_URL = originalUrl;
    }
    globalThis.fetch = originalFetch;
    rmSync(root, { recursive: true, force: true });
  }

  assert.equal(sentUserMessages.length, 0);
  assert.deepEqual(notifications, []);
  assert.equal(fetchCalls.length, 1);
  assert.equal(fetchCalls[0].url, "https://example.invalid/webhook");
  assert.equal(fetchCalls[0].options.method, "POST");
  assert.deepEqual(JSON.parse(fetchCalls[0].options.body), {
    content: "Goal Matrix notifications enabled for this project.",
    event: "session_start",
  });
});
