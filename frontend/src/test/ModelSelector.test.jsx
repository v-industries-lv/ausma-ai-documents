import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ModelSelector from "../components/ModelSelector";
import { getOptions } from "./test-utils";

describe("ModelSelector Component", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function testHarness({ models = [], model: initialModel = null }) {
    let modelListLoaded = 0;
    let timesSetCalled = 0;
    global.fetch.mockImplementation((url, opts) => {
      if (url === "/api/llm_runners/models_with_capabilities") {
        modelListLoaded++;
        return Promise.resolve({
          ok: true,
          json: async () => models,
        });
      } else if (url === "/api/llm_runners/models/refresh") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: "success" }),
        });
      } else {
        throw new Error(
          `unexpected API call on ${url} with options ${JSON.stringify(opts)}`,
        );
      }
    });
    let model = initialModel;
    function setModel(_model) {
      timesSetCalled++;
      if (typeof _model === "function") {
        model = _model(model);
      } else {
        model = _model;
      }
    }
    function getModel() {
      return model;
    }
    async function waitForModelLoad() {
      return await waitFor(() => {
        expect(modelListLoaded).toBeGreaterThan(0);
      });
    }
    function getTimesSetCalled() {
      return timesSetCalled;
    }
    return { getModel, setModel, waitForModelLoad, getTimesSetCalled };
  }

  it("should show all completion options", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
          {
            model: "embedding-model",
            runner_type: "ollama",
            capabilities: ["embedding"],
          },
        ],
        model: "test_model",
      });
    render(<ModelSelector setModel={setModel} model={getModel()} />);
    await waitForModelLoad();
    const llmModel = screen.getByLabelText("LLM model:");
    const values = getOptions(llmModel);
    expect(values).toEqual([
      { value: "first_model", text: "first_model" },
      { value: "test_model", text: "test_model" },
      { value: "other_model", text: "other_model" },
    ]);
    expect(getTimesSetCalled()).toBe(0);
  });

  it("should filter by runner type", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
          {
            model: "debug-MODEL",
            runner_type: "debug",
            capabilities: ["completion", "vision"],
          },
          {
            model: "embedding-model",
            runner_type: "ollama",
            capabilities: ["embedding"],
          },
        ],
        model: "test_model",
      });
    render(
      <ModelSelector
        setModel={setModel}
        model={getModel()}
        runnerType="ollama"
      />,
    );
    await waitForModelLoad();
    const llmModel = screen.getByLabelText("LLM model:");
    const values = getOptions(llmModel);
    expect(values).toEqual([
      { value: "first_model", text: "first_model" },
      { value: "test_model", text: "test_model" },
      { value: "other_model", text: "other_model" },
    ]);
  });

  it("should handle empty list gracefully", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [],
      });
    render(<ModelSelector setModel={setModel} model={getModel()} />);
    await waitForModelLoad();
    const llmModel = screen.getByLabelText("LLM model:");
    const values = getOptions(llmModel);
    expect(values).toEqual([]);
    expect(getTimesSetCalled()).toBe(0);
  });

  it("should render chosen model name", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
        ],
        model: "test_model",
      });
    render(<ModelSelector setModel={setModel} model={getModel()} />);
    await waitForModelLoad();
    expect(getModel()).toBe("test_model");
    const llmModel = screen.getByLabelText("LLM model:");
    expect(llmModel.value).toBe("test_model");
    expect(screen.getByDisplayValue("test_model")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(0);
  });

  it("should update model on selection", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
        ],
        model: "test_model",
      });
    const { rerender } = render(
      <ModelSelector setModel={setModel} model={getModel()} />,
    );
    await waitForModelLoad();
    expect(getModel()).toBe("test_model");
    const llmModel = screen.getByLabelText("LLM model:");
    expect(llmModel.value).toBe("test_model");
    expect(screen.getByDisplayValue("test_model")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(0);

    // select other_model
    fireEvent.change(llmModel, { target: { value: "other_model" } });
    rerender(<ModelSelector setModel={setModel} model={getModel()} />);

    expect(getModel()).toBe("other_model");
    expect(llmModel.value).toBe("other_model");
    expect(screen.getByDisplayValue("other_model")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(1);
  });

  it("should pick first model if not selected", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
        ],
      });

    render(<ModelSelector setModel={setModel} model={getModel()} />);
    await waitForModelLoad();
    expect(getModel()).toBe("first_model");
    const llmModel = screen.getByLabelText("LLM model:");
    expect(llmModel.value).toBe("first_model");
    expect(screen.getByDisplayValue("first_model")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(1);
  });

  it("should keep the selected model after refreshing ", async () => {
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
        ],
        model: "test_model",
      });
    render(<ModelSelector setModel={setModel} model={getModel()} />);
    await waitForModelLoad();
    const button = screen.getByRole("button");
    fireEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    expect(getModel()).toBe("test_model");
    expect(screen.getByDisplayValue("test_model")).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(0);
  });

  it("should keep the selected model even if the model is not on the model list", async () => {
    const selectedModel = "not_on_list";
    const { getModel, setModel, waitForModelLoad, getTimesSetCalled } =
      testHarness({
        models: [
          {
            model: "first_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "test_model",
            runner_type: "ollama",
            capabilities: ["completion"],
          },
          {
            model: "other_model",
            runner_type: "ollama",
            capabilities: ["completion", "vision"],
          },
        ],
        model: selectedModel,
      });
    render(<ModelSelector setModel={setModel} model={getModel()} />);
    await waitForModelLoad();
    // before refresh
    const llmModel = screen.getByLabelText("LLM model:");
    expect(llmModel.title).toMatch(new RegExp(`^${selectedModel}?`));
    expect(llmModel.title).toMatch(
      new RegExp(`Model not found. Check runner.$`),
    );
    expect(getModel()).toBe(selectedModel);

    expect(
      screen.getByDisplayValue("[!] " + selectedModel),
    ).toBeInTheDocument();

    const button = screen.getByRole("button");
    fireEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    // after refresh
    expect(getModel()).toBe(selectedModel);
    expect(llmModel.title).toMatch(new RegExp(`^${selectedModel}?`));
    expect(llmModel.title).toMatch(
      new RegExp(`Model not found. Check runner.$`),
    );
    expect(llmModel.title).toContain("Model not found. Check runner.");
    expect(
      screen.getByDisplayValue("[!] " + selectedModel),
    ).toBeInTheDocument();
    expect(getTimesSetCalled()).toBe(0);
  });
});
