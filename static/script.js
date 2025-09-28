// static/script.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("vitalsForm");
  const msg = document.getElementById("message");
  const downloadBtn = document.getElementById("downloadBtn");
  let lastPatientId = null;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setMessage("Saving vitals...", "info");
    downloadBtn.disabled = true;

    const patient_id = document.getElementById("patient_id").value.trim();
    if (!patient_id) {
      setMessage("Patient ID is required.", "error");
      return;
    }

    const payload = {
      patient_id,
      patient_name: document.getElementById("patient_name").value.trim() || undefined,
      heart_rate: parseInt(document.getElementById("heart_rate").value) || undefined,
      blood_pressure: {
        systolic: parseInt(document.getElementById("systolic").value) || undefined,
        diastolic: parseInt(document.getElementById("diastolic").value) || undefined
      },
      respiratory_rate: parseInt(document.getElementById("respiratory_rate").value) || undefined,
      temperature_c: parseFloat(document.getElementById("temperature_c").value) || undefined,
      oxygen_saturation: parseInt(document.getElementById("oxygen_saturation").value) || undefined,
      notes: document.getElementById("notes").value.trim() || undefined
    };

    // Clean up undefined fields
    Object.keys(payload).forEach(k => (payload[k] === undefined) && delete payload[k]);
    if (payload.blood_pressure) {
      Object.keys(payload.blood_pressure).forEach(k => (payload.blood_pressure[k] === undefined) && delete payload.blood_pressure[k]);
      if (Object.keys(payload.blood_pressure).length === 0) delete payload.blood_pressure;
    }

    try {
      const res = await fetch("/vitals", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned ${res.status}`);
      }
      
      const data = await res.json();
      setMessage("✅ Vitals saved successfully! You can now download the PDF report.", "success");
      lastPatientId = data.patient_id;
      downloadBtn.disabled = false;

    } catch (err) {
      console.error("Save error:", err);
      setMessage("❌ Failed to save vitals: " + err.message, "error");
    }
  });

  // Download button handler
  downloadBtn.addEventListener("click", async () => {
    if (!lastPatientId) return;
    
    downloadBtn.disabled = true;
    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<span class="loading"></span> Preparing PDF...';
    
    setMessage("Generating PDF report...", "info");

    try {
      const res = await fetch(`/vitals/${encodeURIComponent(lastPatientId)}/pdf`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      
      const blob = await res.blob();
      const filename = `${lastPatientId}_vitals_report.pdf`;
      const url = window.URL.createObjectURL(blob);
      
      // Create download link
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      setMessage("✅ PDF downloaded successfully!", "success");
      
    } catch (err) {
      console.error("Download error:", err);
      setMessage("❌ Failed to download PDF: " + err.message, "error");
    } finally {
      downloadBtn.disabled = false;
      downloadBtn.innerHTML = originalText;
    }
  });

  // Helper function to set message
  function setMessage(text, type = "info") {
    msg.textContent = text;
    msg.className = "";
    if (type === "success") msg.classList.add("success");
    if (type === "error") msg.classList.add("error");
  }

  // Add input validation
  const numberInputs = document.querySelectorAll('input[type="number"]');
  numberInputs.forEach(input => {
    input.addEventListener('input', (e) => {
      const value = e.target.value;
      if (value && (value < 0 || value > 300)) {
        e.target.style.borderColor = '#ef4444';
      } else {
        e.target.style.borderColor = '';
      }
    });
  });
});