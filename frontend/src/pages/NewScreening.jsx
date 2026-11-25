import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitScreening } from "../services/api";

const MAX_UPLOAD_MB = 15;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/jpg"];

export default function NewScreening() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [fieldEye, setFieldEye] = useState("OD"); // OD (Right), OS (Left)
  const [centering, setCentering] = useState("macula"); // macula, disc
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  function handleFileSelection(file) {
    setErrorMessage(null);
    if (!file) return;

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setErrorMessage("Invalid file format. Please upload a JPEG or PNG retinal fundus photograph.");
      return;
    }

    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_UPLOAD_MB) {
      setErrorMessage(`File size (${fileSizeMB.toFixed(1)} MB) exceeds maximum allowed limit of ${MAX_UPLOAD_MB} MB.`);
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  }

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage("Please select a fundus photograph to submit.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await submitScreening(selectedFile);
      if (response && response.case_id) {
        navigate(`/screening/${response.case_id}`);
      } else {
        throw new Error("Screening completed but no Case ID was returned by the server.");
      }
    } catch (err) {
      setErrorMessage(err.message || "Failed to process retinal screening. Ensure backend is running.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-container new-screening-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">New Retinal Screening</h1>
          <p className="page-subtitle">Upload digital color fundus photograph for automated quality assessment and DR triage.</p>
        </div>
      </div>

      <div className="screening-form-layout">
        <form onSubmit={handleSubmit} className="upload-form">
          {/* Metadata Controls */}
          <div className="form-card metadata-card">
            <h3>Examination Details</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="eye-select">Eye Examined:</label>
                <select
                  id="eye-select"
                  value={fieldEye}
                  onChange={(e) => setFieldEye(e.target.value)}
                  className="form-control"
                  disabled={isSubmitting}
                >
                  <option value="OD">Right Eye (OD - Oculus Dexter)</option>
                  <option value="OS">Left Eye (OS - Oculus Sinister)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="centering-select">Camera Field Centering:</label>
                <select
                  id="centering-select"
                  value={centering}
                  onChange={(e) => setCentering(e.target.value)}
                  className="form-control"
                  disabled={isSubmitting}
                >
                  <option value="macula">Field 1: Macula-Centered (45°)</option>
                  <option value="disc">Field 2: Optic Disc-Centered (45°)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Drag & Drop Zone */}
          <div
            className={`dropzone-card ${dragActive ? "drag-active" : ""} ${selectedFile ? "has-file" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png"
              className="file-input-hidden"
              onChange={(e) => e.target.files && handleFileSelection(e.target.files[0])}
            />

            {previewUrl ? (
              <div className="preview-container">
                <img src={previewUrl} alt="Retinal Fundus Preview" className="preview-image" />
                <div className="preview-meta">
                  <p className="file-name"><strong>Selected:</strong> {selectedFile?.name}</p>
                  <p className="file-size">({(selectedFile?.size / (1024 * 1024)).toFixed(2)} MB)</p>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline mt-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                  >
                    Change Image
                  </button>
                </div>
              </div>
            ) : (
              <div className="dropzone-prompt">
                <div className="dropzone-icon">📷</div>
                <h3>Drag and drop retinal fundus image here</h3>
                <p>or click to browse local files (JPEG, PNG up to 15 MB)</p>
                <span className="btn btn-secondary mt-2">Select Fundus Photo</span>
              </div>
            )}
          </div>

          {/* Error Feedback */}
          {errorMessage && (
            <div className="error-banner" role="alert">
              <span className="error-icon">❌</span>
              <p>{errorMessage}</p>
            </div>
          )}

          {/* Action Footer */}
          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={!selectedFile || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner-inline"></span>
                  Analyzing Fundus Image...
                </>
              ) : (
                "Run Screening Analysis →"
              )}
            </button>
          </div>
        </form>

        {/* Clinical Guidelines Sidebar */}
        <aside className="guidelines-card">
          <h3>Image Capture Protocol</h3>
          <ul>
            <li><strong>Adequate Pupil Dilation:</strong> Ensure $\ge 4$ mm pupil diameter for non-mydriatic cameras.</li>
            <li><strong>Focus & Illumination:</strong> Check that retinal vessels crossing the optic disc appear crisp.</li>
            <li><strong>Corneal Glare:</strong> Angle camera slightly to avoid flash reflection over the fovea.</li>
            <li><strong>Privacy Notice:</strong> Do not upload images containing patient name overlays or embedded PHI.</li>
          </ul>
        </aside>
      </div>
    </div>
  );
}

