import { useState } from "react";

import {
  generateBasicReport,
  generateStandardReport,
  generatePremiumReport,
} from "../services/planService";

export default function PlanTest() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState("");

  const downloadPDF = (blob, filename) => {
    const pdfUrl = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = pdfUrl;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(pdfUrl);
  };


  const handleBasic = async () => {
    try {
      setLoading("basic");

      const blob = await generateBasicReport(url);

      downloadPDF(
        blob,
        "TestPilot_Basic_Report.pdf"
      );

    } catch (error) {
      alert(error.message);
    } finally {
      setLoading("");
    }
  };


  const handleStandard = async () => {
    try {
      setLoading("standard");

      const blob = await generateStandardReport(url);

      downloadPDF(
        blob,
        "TestPilot_Standard_Report.pdf"
      );

    } catch (error) {
      alert(error.message);
    } finally {
      setLoading("");
    }
  };


  const handlePremium = async () => {
    try {
      setLoading("premium");

      const blob = await generatePremiumReport(url);

      downloadPDF(
        blob,
        "TestPilot_Premium_Report.pdf"
      );

    } catch (error) {
      alert(error.message);
    } finally {
      setLoading("");
    }
  };


  return (
    <div style={{ padding: "40px" }}>

      <h1>TestPilot Plan API Test</h1>

      <input
        type="url"
        placeholder="https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{
          width: "400px",
          padding: "10px",
          marginBottom: "20px",
        }}
      />

      <br />

      <button
        onClick={handleBasic}
        disabled={loading !== ""}
      >
        {loading === "basic"
          ? "Generating..."
          : "Basic Report"}
      </button>

      {" "}

      <button
        onClick={handleStandard}
        disabled={loading !== ""}
      >
        {loading === "standard"
          ? "Generating..."
          : "Standard Report"}
      </button>

      {" "}

      <button
        onClick={handlePremium}
        disabled={loading !== ""}
      >
        {loading === "premium"
          ? "Generating..."
          : "Premium Report"}
      </button>

    </div>
  );
}