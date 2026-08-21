import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Chat } from "../pages/Chat";

vi.mock(import("../socket"), () => {
  const channelObject = vi.fn(() => ({
    on: () => {},
    off: () => {},
    emit: () => {},
  }));
  async function on(channel, fn) {
    (await channelObject(channel)).on(fn);
  }
  async function off(channel, fn) {
    (await channelObject(channel)).off(fn);
  }
  async function emit(channel, message) {
    (await channelObject(channel)).emit(message);
  }
  return {
    socket: {
      on,
      off,
      emit,
      channelObject,
    },
  };
});
import { socket } from "../socket";

describe("Chat", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function testHarness({
    roomId,
    roomDefaults = {},
    roomDetails = {},
    history = [],
  }) {
    let historyLoaded = 0;
    global.fetch.mockImplementation((url, opts) => {
      if (url === "/api/config/room_defaults") {
        return Promise.resolve({
          ok: true,
          json: async () => roomDefaults,
        });
      } else if (url === `/api/room/${roomId}`) {
        return Promise.resolve({
          ok: true,
          json: async () => roomDetails,
        });
      } else if (url === `/api/room/${roomId}/progress`) {
        return Promise.resolve({
          ok: true,
          json: async () => {},
        });
      } else if (url === `/api/room_history/${roomId}`) {
        historyLoaded++;
        return Promise.resolve({
          ok: true,
          json: async () => history,
        });
      } else if (url === `/api/room/${roomId}/stop`) {
        return Promise.resolve({
          ok: true,
          json: async () => {},
        });
      } else if (url === `/api/upload_chat_files` && opts?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: async () => {},
        });
      } else {
        throw new Error(
          `unexpected API call on ${url} with options ${JSON.stringify(opts)}`,
        );
      }
    });
    async function waitForHistoryLoad() {
      return await waitFor(() => {
        historyLoaded > 0;
      });
    }

    const channels = {};
    socket.channelObject.mockImplementation(async (name) => {
      let o = channels[name];
      if (!o) {
        o = channels[name] = {
          messages: [],
          listeners: [],
          on: function (fn) {
            this.listeners.push(fn);
          },
          off: function (fn) {
            this.listeners = this.listeners.filter((fx) => fx !== fn);
          },
          emit: function (msg) {
            this.messages.push(msg);
          },
          send: function (msg) {
            this.listeners.forEach((l) => l(msg));
          },
        };
      }
      return o;
    });

    return { channels, waitForHistoryLoad };
  }
  it("should handle empty history", async () => {
    const roomId = "101";
    const { channels, waitForHistoryLoad } = testHarness({
      roomId,
      history: [],
    });
    render(<Chat roomId={roomId} />);
    await waitForHistoryLoad();
    // console.dir(channels, { depth: null });
    // chat should signal joining the room , so it gets updates
    expect(channels.join_room.messages).toContainEqual({ room_id: roomId });
  });
});
