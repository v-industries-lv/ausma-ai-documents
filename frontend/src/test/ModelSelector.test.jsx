import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ModelSelector from "../components/ModelSelector";

describe("ModelSelector Component", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should render chosen model name", async () => {
    global.fetch.mockImplementation((url, opts) => {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          chat_models: ["first_model", "test_model", "other_model"],
        }),
      });
    });
    // component relies on external state for the selected model
    let model = "test_model";
    function setModel(_model) {
      if (typeof _model === "function") {
        model = _model(model);
      } else {
        model = _model;
      }
    }
    render(<ModelSelector setModel={setModel} model={model} />);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    expect(model).toBe("test_model");
    expect(screen.getByText("test_model")).toBeInTheDocument();
    expect(screen.getByDisplayValue("test_model")).toBeInTheDocument();
  });

  it("should pick first model if not selected", async () => {
    global.fetch.mockImplementation((url, opts) => {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          chat_models: ["first_model", "test_model", "other_model"],
        }),
      });
    });
    // component relies on external state for the selected model
    let model = null;
    function setModel(_model) {
      if (typeof _model === "function") {
        model = _model(model);
      } else {
        model = _model;
      }
    }
    render(<ModelSelector setModel={setModel} model={model} />);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    expect(model).toBe("first_model");
    expect(screen.getByText("first_model")).toBeInTheDocument();
    expect(screen.getByDisplayValue("first_model")).toBeInTheDocument();
  });

  it("should keep the selected model after refreshing ", async () => {
    global.fetch.mockImplementation((url, opts) => {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          chat_models: ["first_model", "test_model", "other_model"],
        }),
      });
    });
    // component relies on external state for the selected model
    let model = "test_model";
    function setModel(_model) {
      if (typeof _model === "function") {
        model = _model(model);
      } else {
        model = _model;
      }
    }
    render(<ModelSelector setModel={setModel} model={model} />);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    const button = screen.getByRole("button");
    fireEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText("Refreshing...")).not.toBeInTheDocument();
    });
    expect(model).toBe("test_model");
    expect(screen.getByDisplayValue("test_model")).toBeInTheDocument();
  });
});
