# Example: Handler Test

Complete test file for a flow node handler. This example tests a `notifyHandler` that sends notifications through various channels.

---

## File: lib/runtime/handlers/__tests__/notify-handler.test.ts

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { notifyHandler } from "@/lib/runtime/handlers/notify-handler";
import type { RuntimeContext, FlowNode } from "@/types";

// ============================================================================
// MOCKS
// ============================================================================

// Mock channel services
vi.mock("@/lib/channels/email", () => ({
  sendEmail: vi.fn(),
}));

vi.mock("@/lib/channels/sms", () => ({
  sendSMS: vi.fn(),
}));

vi.mock("@/lib/usage", () => ({
  trackUsage: vi.fn(),
}));

// ============================================================================
// IMPORTS & MOCK CASTING
// ============================================================================

import { sendEmail } from "@/lib/channels/email";
import { sendSMS } from "@/lib/channels/sms";
import { trackUsage } from "@/lib/usage";

const mockSendEmail = vi.mocked(sendEmail);
const mockSendSMS = vi.mocked(sendSMS);
const mockTrackUsage = vi.mocked(trackUsage);

// ============================================================================
// FACTORIES
// ============================================================================

/**
 * Create a runtime context with sensible defaults
 */
function makeContext(overrides?: Partial<RuntimeContext>): RuntimeContext {
  return {
    conversationId: "conv-123",
    agentId: "agent-123",
    workspaceId: "ws-123",
    flowContent: {
      nodes: [],
      edges: [],
    },
    currentNodeId: "node-notify",
    variables: {
      user_name: "Alice",
      user_email: "alice@example.com",
      user_phone: "+1234567890",
      order_number: "ORD-12345",
      order_total: "99.99",
      support_url: "https://support.example.com",
    },
    messageHistory: [
      { role: "user", content: "I need help with my order" },
      { role: "assistant", content: "I'd be happy to help! What's your order number?" },
      { role: "user", content: "ORD-12345" },
    ],
    ...overrides,
  };
}

/**
 * Create a flow node with sensible defaults
 */
function makeNode(overrides?: Partial<FlowNode>): FlowNode {
  return {
    id: "node-notify",
    type: "notify",
    position: { x: 0, y: 0 },
    data: {
      label: "Send Notification",
      channel: "email",
      message: "Hello {{user_name}}!",
      subject: "Notification",
      ...overrides?.data,
    },
    ...overrides,
  };
}

// ============================================================================
// TESTS
// ============================================================================

describe("notifyHandler", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --------------------------------------------------------------------------
  // Template Resolution Tests
  // --------------------------------------------------------------------------

  describe("Template Resolution", () => {
    it("should resolve single template variable", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          label: "Welcome",
          channel: "email",
          message: "Hello {{user_name}}!",
          subject: "Welcome",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(true);
      expect(mockSendEmail).toHaveBeenCalledWith({
        to: "alice@example.com",
        subject: "Welcome",
        body: "Hello Alice!",
      });
    });

    it("should resolve multiple template variables", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          label: "Order Confirmation",
          channel: "email",
          message:
            "Hi {{user_name}}, your order {{order_number}} totaling ${{order_total}} has been confirmed!",
          subject: "Order {{order_number}} Confirmed",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      await notifyHandler(context, node);

      expect(mockSendEmail).toHaveBeenCalledWith({
        to: "alice@example.com",
        subject: "Order ORD-12345 Confirmed",
        body: "Hi Alice, your order ORD-12345 totaling $99.99 has been confirmed!",
      });
    });

    it("should handle missing template variables gracefully", async () => {
      const context = makeContext({
        variables: {
          user_name: "Alice",
          // Missing user_email, order_number
        },
      });

      const node = makeNode({
        data: {
          label: "Incomplete Data",
          channel: "email",
          message: "Hello {{user_name}}, order {{order_number}} is ready!",
          subject: "Order Ready",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      await notifyHandler(context, node);

      // Should replace missing variables with empty string
      expect(mockSendEmail).toHaveBeenCalledWith({
        to: expect.any(String),
        subject: "Order Ready",
        body: "Hello Alice, order  is ready!",
      });
    });

    it("should preserve non-variable text", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          label: "Support Link",
          channel: "email",
          message:
            "Need help? Visit {{support_url}} or reply to this email.",
          subject: "Help Available",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      await notifyHandler(context, node);

      expect(mockSendEmail).toHaveBeenCalledWith({
        to: "alice@example.com",
        subject: "Help Available",
        body: "Need help? Visit https://support.example.com or reply to this email.",
      });
    });
  });

  // --------------------------------------------------------------------------
  // Channel Tests
  // --------------------------------------------------------------------------

  describe("Email Channel", () => {
    it("should send email notification", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          label: "Email Notification",
          channel: "email",
          message: "Your order is ready!",
          subject: "Order Ready",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(true);
      expect(result.notificationId).toBe("email-123");
      expect(mockSendEmail).toHaveBeenCalledWith({
        to: "alice@example.com",
        subject: "Order Ready",
        body: "Your order is ready!",
      });
    });

    it("should handle email send failure", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          channel: "email",
          message: "Test",
          subject: "Test",
        },
      });

      mockSendEmail.mockRejectedValue(new Error("Email service unavailable"));

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toBe("Email service unavailable");
    });

    it("should fail when email address is missing", async () => {
      const context = makeContext({
        variables: {
          user_name: "Alice",
          // Missing user_email
        },
      });

      const node = makeNode({
        data: {
          channel: "email",
          message: "Test",
          subject: "Test",
        },
      });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toContain("email address");
      expect(mockSendEmail).not.toHaveBeenCalled();
    });
  });

  describe("SMS Channel", () => {
    it("should send SMS notification", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          label: "SMS Notification",
          channel: "sms",
          message: "Your order {{order_number}} is out for delivery!",
        },
      });

      mockSendSMS.mockResolvedValue({ id: "sms-456" });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(true);
      expect(result.notificationId).toBe("sms-456");
      expect(mockSendSMS).toHaveBeenCalledWith({
        to: "+1234567890",
        body: "Your order ORD-12345 is out for delivery!",
      });
    });

    it("should handle SMS send failure", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          channel: "sms",
          message: "Test",
        },
      });

      mockSendSMS.mockRejectedValue(new Error("SMS gateway error"));

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toBe("SMS gateway error");
    });

    it("should fail when phone number is missing", async () => {
      const context = makeContext({
        variables: {
          user_name: "Alice",
          // Missing user_phone
        },
      });

      const node = makeNode({
        data: {
          channel: "sms",
          message: "Test",
        },
      });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toContain("phone number");
      expect(mockSendSMS).not.toHaveBeenCalled();
    });
  });

  // --------------------------------------------------------------------------
  // Flow Control Tests
  // --------------------------------------------------------------------------

  describe("Flow Control", () => {
    it("should not wait for input", async () => {
      const context = makeContext();
      const node = makeNode();

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.waitForInput).toBe(false);
    });

    it("should determine next node from edges", async () => {
      const context = makeContext({
        flowContent: {
          nodes: [
            { id: "node-notify", type: "notify", position: { x: 0, y: 0 }, data: {} },
            { id: "node-end", type: "end", position: { x: 0, y: 200 }, data: {} },
          ],
          edges: [
            {
              id: "e1",
              source: "node-notify",
              target: "node-end",
            },
          ],
        },
      });

      const node = makeNode();
      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.nextNodeId).toBe("node-end");
    });

    it("should handle conditional edges based on success/failure", async () => {
      const context = makeContext({
        flowContent: {
          nodes: [],
          edges: [
            {
              id: "e-success",
              source: "node-notify",
              target: "node-success",
              label: "success",
            },
            {
              id: "e-failure",
              source: "node-notify",
              target: "node-error",
              label: "error",
            },
          ],
        },
      });

      const node = makeNode();
      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.nextNodeId).toBe("node-success");
    });

    it("should route to error node on failure", async () => {
      const context = makeContext({
        flowContent: {
          nodes: [],
          edges: [
            {
              id: "e-success",
              source: "node-notify",
              target: "node-success",
              label: "success",
            },
            {
              id: "e-failure",
              source: "node-notify",
              target: "node-error",
              label: "error",
            },
          ],
        },
      });

      const node = makeNode();
      mockSendEmail.mockRejectedValue(new Error("Send failed"));

      const result = await notifyHandler(context, node);

      expect(result.nextNodeId).toBe("node-error");
    });

    it("should not update variables", async () => {
      const context = makeContext();
      const node = makeNode();

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.updatedVariables).toBeUndefined();
    });
  });

  // --------------------------------------------------------------------------
  // Usage Tracking Tests
  // --------------------------------------------------------------------------

  describe("Usage Tracking", () => {
    it("should track notification usage on success", async () => {
      const context = makeContext();
      const node = makeNode();

      mockSendEmail.mockResolvedValue({ id: "email-123" });
      mockTrackUsage.mockResolvedValue(undefined);

      await notifyHandler(context, node);

      expect(mockTrackUsage).toHaveBeenCalledWith(
        "ws-123",
        "NOTIFICATION",
        1
      );
    });

    it("should not track usage on failure", async () => {
      const context = makeContext();
      const node = makeNode();

      mockSendEmail.mockRejectedValue(new Error("Send failed"));

      await notifyHandler(context, node);

      expect(mockTrackUsage).not.toHaveBeenCalled();
    });
  });

  // --------------------------------------------------------------------------
  // Edge Cases
  // --------------------------------------------------------------------------

  describe("Edge Cases", () => {
    it("should handle empty message", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          channel: "email",
          message: "",
          subject: "Empty",
        },
      });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toContain("Message cannot be empty");
      expect(mockSendEmail).not.toHaveBeenCalled();
    });

    it("should handle whitespace-only message", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          channel: "email",
          message: "   \n  \t  ",
          subject: "Whitespace",
        },
      });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toContain("Message cannot be empty");
    });

    it("should handle very long messages", async () => {
      const context = makeContext();
      const longMessage = "A".repeat(10000);

      const node = makeNode({
        data: {
          channel: "email",
          message: longMessage,
          subject: "Long",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(true);
      expect(mockSendEmail).toHaveBeenCalledWith({
        to: expect.any(String),
        subject: "Long",
        body: longMessage,
      });
    });

    it("should handle special characters in templates", async () => {
      const context = makeContext({
        variables: {
          user_name: "Alice & Bob",
          special_chars: "<script>alert('xss')</script>",
        },
      });

      const node = makeNode({
        data: {
          channel: "email",
          message: "Hello {{user_name}}, code: {{special_chars}}",
          subject: "Special Chars",
        },
      });

      mockSendEmail.mockResolvedValue({ id: "email-123" });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(true);
      // Should not escape HTML (handler should sanitize if needed)
      expect(mockSendEmail).toHaveBeenCalledWith({
        to: expect.any(String),
        subject: "Special Chars",
        body: "Hello Alice & Bob, code: <script>alert('xss')</script>",
      });
    });

    it("should handle invalid channel", async () => {
      const context = makeContext();
      const node = makeNode({
        data: {
          channel: "invalid-channel",
          message: "Test",
        },
      });

      const result = await notifyHandler(context, node);

      expect(result.success).toBe(false);
      expect(result.error).toContain("Unsupported channel");
    });
  });
});
```

---

## Key Takeaways

1. **Factories are essential**: `makeContext` and `makeNode` provide sensible defaults and reduce test boilerplate
2. **Override only what matters**: Pass partial overrides to factories for specific test scenarios
3. **Group related tests**: Use nested `describe` blocks to organize by feature (template resolution, channels, flow control)
4. **Test the happy path**: Verify successful execution with mocked dependencies
5. **Test error states**: Mock failures and verify graceful error handling
6. **Test edge cases**: Empty values, whitespace, missing data, special characters, invalid input
7. **Verify side effects**: Check that external services (email, SMS) were called with correct params
8. **Verify flow control**: Test `nextNodeId`, `waitForInput`, `updatedVariables`
9. **Verify usage tracking**: Ensure usage is tracked on success but not on failure
10. **Clear mock setup**: Always `vi.clearAllMocks()` in `beforeEach` to isolate tests
