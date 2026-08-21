import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import AssistantSelector from "../components/AssistantSelector";
import { getOptions } from "./test-utils";

describe("AssitantSelector Component", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function testHarness({
    assistants = [],
    assistant: initialAssistant = null,
  }) {
    let assistantListLoaded = 0;
    let timesSetCalled = 0;
    global.fetch.mockImplementation((url, opts) => {
      if (url === "/api/config/assistants") {
        assistantListLoaded++;
        return Promise.resolve({
          ok: true,
          json: async () => assistants,
        });
      } else {
        throw new Error(
          `unexpected API call on ${url} with options ${JSON.stringify(opts)}`,
        );
      }
    });
    let assistant = initialAssistant;
    function setAssistant(_assistant) {
      timesSetCalled++;
      if (typeof _assistant === "function") {
        assistant = _assistant(assistant);
      } else {
        assistant = _assistant;
      }
    }
    function getAssistant() {
      return assistant;
    }
    function getTimesSetCalled() {
      return timesSetCalled;
    }
    async function waitForAssistantLoad() {
      return await waitFor(() => {
        expect(assistantListLoaded).toBeGreaterThan(0);
      });
    }
    return {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    };
  }

  const exampleAssitants = {
    Ausma: {
      name: "Ausma",
      options: {
        seed: 42,
        num_predict: 8000,
        num_ctx: 16000,
      },
      model: "gemma4:latest",
      system_prompt:
        "You are a helpful assistant. Provide a conversational answer. Do not respond with anything that might cause XSS. If you don't know the answer, just say \"I do not know.\" Don't make up an answer. ",
      runner_type: "ollama",
      history_mode: "full",
      rag_settings: {
        rag_document_count: 20,
        rag_similarity_score_threshold: 0.8,
        rag_score_margin: 0.2,
        rag_cosine_distance_irrelevance_threshold: 1,
      },
      thinking_flag: "false",
    },
    Astra: {
      name: "Astra",
      options: {
        seed: 42,
        num_predict: 8000,
        num_ctx: 16000,
      },
      model: "qwen3-vl:latest",
      system_prompt:
        "You are a helpful assistant. Provide a conversational answer. Do not respond with anything that might cause XSS. If you don't know the answer, just say \"I do not know.\" Don't make up an answer. ",
      runner_type: "ollama",
      history_mode: "full",
      rag_settings: {
        rag_document_count: 20,
        rag_similarity_score_threshold: 0.8,
        rag_score_margin: 0.2,
        rag_cosine_distance_irrelevance_threshold: 1,
      },
      thinking_flag: "high",
    },
  };

  it("should show all completion options", async () => {
    const {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    } = testHarness({
      assistants: [...Object.values(exampleAssitants)],
      assistant: "Astra",
    });
    render(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    await waitForAssistantLoad();
    const assistant = screen.getByLabelText("Assistant:");
    const values = getOptions(assistant);
    expect(values).toEqual([
      { value: "Ausma", text: "Ausma" },
      { value: "Astra", text: "Astra" },
    ]);
  });

  it("should handle empty list gracefully", async () => {
    const {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    } = testHarness({
      assistants: [],
    });
    render(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    await waitForAssistantLoad();
    const assistant = screen.getByLabelText("Assistant:");
    const values = getOptions(assistant);
    expect(values).toEqual([]);
    expect(getTimesSetCalled()).toBe(0);
  });

  it("should render chosen assistant name", async () => {
    const {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    } = testHarness({
      assistants: [...Object.values(exampleAssitants)],
      assistant: "Astra",
    });
    render(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    await waitForAssistantLoad();
    expect(getAssistant()).toEqual("Astra");
    const assistant = screen.getByLabelText("Assistant:");
    expect(assistant.value).toEqual("Astra");
    expect(screen.getByDisplayValue("Astra")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(0);
  });

  it("should update assitant on selection", async () => {
    const {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    } = testHarness({
      assistants: [...Object.values(exampleAssitants)],
      assistant: "Astra",
    });
    const { rerender } = render(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    await waitForAssistantLoad();
    expect(getAssistant()).toEqual("Astra");
    const assistant = screen.getByLabelText("Assistant:");
    expect(assistant.value).toEqual("Astra");
    expect(screen.getByDisplayValue("Astra")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(0);

    // select Ausma
    fireEvent.change(assistant, { target: { value: "Ausma" } });
    expect(getAssistant()).toEqual("Ausma");
    rerender(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    expect(assistant.value).toEqual("Ausma");
    expect(screen.getByDisplayValue("Ausma")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(1);
  });

  it("should pick first assistant if none selected", async () => {
    const {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    } = testHarness({
      assistants: [...Object.values(exampleAssitants)],
    });

    render(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    await waitForAssistantLoad();
    expect(getAssistant()).toEqual("Ausma");
    const assistant = screen.getByLabelText("Assistant:");
    expect(assistant.value).toEqual("Ausma");
    expect(screen.getByDisplayValue("Ausma")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(1);
  });

  it("should keep the selected assistant after refreshing ", async () => {
    const {
      getAssistant,
      setAssistant,
      waitForAssistantLoad,
      getTimesSetCalled,
    } = testHarness({
      assistants: [...Object.values(exampleAssitants)],
      assistant: "Astra",
    });
    render(
      <AssistantSelector
        setAssistant={setAssistant}
        assistant={getAssistant()}
      />,
    );
    await waitForAssistantLoad();
    const button = screen.getByRole("button");
    fireEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    expect(getAssistant()).toEqual("Astra");
    const assistant = screen.getByLabelText("Assistant:");
    expect(assistant.value).toEqual("Astra");
    expect(screen.getByDisplayValue("Astra")).toBeInTheDocument();

    expect(getTimesSetCalled()).toBe(0);
  });
});
