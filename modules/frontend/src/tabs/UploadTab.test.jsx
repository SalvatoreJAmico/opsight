import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import UploadTab from "./UploadTab";
import { triggerPipeline } from "../api/client";

const expectedDefaultBaseUrl = import.meta.env.DEV ? "/api-local" : "/api-cloud";

vi.mock("../api/client", () => ({
  triggerPipeline: vi.fn(),
}));

describe("UploadTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("validates blank access code before submit", async () => {
    render(<UploadTab />);

    fireEvent.change(screen.getByLabelText("Access Code"), {
      target: { value: "   " },
    });

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    expect(await screen.findByText("Access code is required.")).toBeInTheDocument();
    expect(triggerPipeline).not.toHaveBeenCalled();
  });

  it("validates blank source path before submit", async () => {
    render(<UploadTab />);

    fireEvent.change(screen.getByLabelText("Source Path"), {
      target: { value: "" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    expect(await screen.findByText("Source path is required.")).toBeInTheDocument();
    expect(triggerPipeline).not.toHaveBeenCalled();
  });

  it("shows loading state while request is in progress", async () => {
    triggerPipeline.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, data: { status: "processed" } }), 20)),
    );

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    expect(await screen.findByText("Submitting pipeline request...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Running..." })).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText(/Pipeline triggered successfully/)).toBeInTheDocument();
    });
  });

  it("handles invalid access code response", async () => {
    triggerPipeline.mockResolvedValue({
      ok: false,
      status: 403,
      error: "Invalid or missing upload access code",
      data: null,
    });

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    expect(await screen.findByText("Invalid or missing access code.")).toBeInTheDocument();
  });

  it("renders success and response payload when trigger succeeds", async () => {
    triggerPipeline.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: {
        status: "processed",
        records_ingested: 3,
      },
    });

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    expect(await screen.findByText(/Pipeline triggered successfully/)).toBeInTheDocument();
    expect(screen.getByText("Response")).toBeInTheDocument();
    expect(screen.getByText(/records_ingested/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({
        access_code: "demo-code",
      }),
      expect.objectContaining({ baseUrl: expectedDefaultBaseUrl }),
    );
  });

  it("switches to local target when local sample is selected", async () => {
    triggerPipeline.mockResolvedValue({
      ok: false,
      status: 0,
      error: "Network error",
      data: null,
    });

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Use Local Sample" }));
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    expect(await screen.findByText(/Local API is unavailable/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({
        source_path: "data/opsight_sample_sales.csv",
      }),
      expect.objectContaining({ baseUrl: "/api-local" }),
    );
  });
});
