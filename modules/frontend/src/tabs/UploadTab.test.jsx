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

  it("shows loading state while request is in progress", async () => {
    triggerPipeline.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, data: { status: "processed" } }), 20)),
    );

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(screen.getByRole("button", { name: "Running..." })).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText(/Pipeline triggered successfully/)).toBeInTheDocument();
    });
  });

  it("handles API error response", async () => {
    triggerPipeline.mockResolvedValue({
      ok: false,
      status: 500,
      error: "Internal server error",
      data: null,
    });

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText("Internal server error")).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Pipeline triggered successfully/)).toBeInTheDocument();
    expect(screen.getByText("Response")).toBeInTheDocument();
    expect(screen.getByText(/records_ingested/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({ target: expectedDefaultBaseUrl === "/api-local" ? "local" : "cloud" }),
      expect.objectContaining({ baseUrl: expectedDefaultBaseUrl }),
    );
  });

  it("switches to local target when Local button is clicked", async () => {
    triggerPipeline.mockResolvedValue({
      ok: false,
      status: 0,
      error: "Network error",
      data: null,
    });

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Local" }));
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Local API is unavailable/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({ target: "local" }),
      expect.objectContaining({ baseUrl: "/api-local" }),
    );
  });

  it("switches to cloud target when Cloud button is clicked", async () => {
    triggerPipeline.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: { status: "processed" },
    });

    render(<UploadTab />);

    fireEvent.click(screen.getByRole("button", { name: "Cloud" }));
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Pipeline triggered successfully on deployed API/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({ target: "cloud" }),
      expect.objectContaining({ baseUrl: "/api-cloud" }),
    );
  });
});
