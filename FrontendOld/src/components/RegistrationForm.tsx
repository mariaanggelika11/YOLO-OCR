import React, { useState, useEffect } from "react";
import { AlertCircle } from "lucide-react";

/* ================================
   BACKEND STRUCTURE
================================ */
interface BackendParsedData {
  firstName?: string;
  lastName?: string;
  address?: string;
  dateOfBirth?: string;
  sex?: string;
  passportNumber?: string;
  licenseNumber?: string;
  faceImage?: string;
  StateName?: string;
}

/* ================================
   FORM STRUCTURE
================================ */
interface FormData {
  firstName: string;
  lastName: string;
  address: string;
  dateOfBirth: string;
  sex: string;
  passportNumber: string;
  licenseNumber: string;
  stateName: string;
  faceImage?: string;
}

interface RegistrationFormProps {
  initialData: BackendParsedData;
}

const emptyForm: FormData = {
  firstName: "",
  lastName: "",
  address: "",
  dateOfBirth: "",
  sex: "",
  passportNumber: "",
  licenseNumber: "",
  stateName: "",
};

/* ================================
   DATE FORMATTER
================================ */
function convertToISO(dateStr?: string): string {
  if (!dateStr) return "";
  const parts = dateStr.split("/");
  if (parts.length !== 3) return "";
  const [mm, dd, yyyy] = parts;
  return `${yyyy}-${mm.padStart(2, "0")}-${dd.padStart(2, "0")}`;
}

const RegistrationForm: React.FC<RegistrationFormProps> = ({ initialData }) => {
  const [form, setForm] = useState<FormData>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, boolean>>>({});

  useEffect(() => {
    if (!initialData || Object.keys(initialData).length === 0) {
      setForm(emptyForm);
      setErrors({});
      return;
    }

    const mapped: FormData = {
      firstName: initialData.firstName || "",
      lastName: initialData.lastName || "",
      address: initialData.address || "",
      dateOfBirth: convertToISO(initialData.dateOfBirth),
      sex: initialData.sex || "",
      passportNumber: initialData.passportNumber || "",
      licenseNumber: initialData.licenseNumber || "",
      stateName: initialData.StateName || "",
      faceImage: initialData.faceImage,
    };

    setForm(mapped);

    const newErrors: Partial<Record<keyof FormData, boolean>> = {};
    Object.entries(mapped).forEach(([key, value]) => {
      if (!value || String(value).trim() === "") {
        newErrors[key as keyof FormData] = true;
      }
    });

    setErrors(newErrors);
  }, [initialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));

    if (value.trim() !== "") {
      setErrors((prev) => ({ ...prev, [name]: false }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Saved Data:\n${JSON.stringify(form, null, 2)}`);
  };

  const inputClass = (field: keyof FormData) =>
    `w-full px-3 py-2 bg-gray-50 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
      errors[field] ? "border-red-400 ring-red-200" : "border-gray-300"
    }`;

  const errorText = (field: keyof FormData) =>
    errors[field] && (
      <p className="flex items-center gap-1 text-xs text-red-600 mt-1">
        <AlertCircle size={14} />
        This field needs to be filled or corrected.
      </p>
    );

  return (
    <div className="bg-white p-6 rounded-2xl shadow-lg w-full max-w-lg animate-fade-in">

      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-3">
        <div className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">
          2
        </div>
        Extracted Information
      </h2>

      {/* FACE IMAGE */}
      {form.faceImage && (
        <div className="flex justify-center mb-4">
          <div className="relative">
            <img
              src={`data:image/jpeg;base64,${form.faceImage}`}
              alt="Face Preview"
              className="w-24 h-32 object-cover rounded-lg border shadow"
            />
            <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 text-xs bg-indigo-600 text-white px-2 py-0.5 rounded">
              Auto
            </span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">

        {/* NAME */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              First Name
            </label>
            <input
              name="firstName"
              value={form.firstName}
              onChange={handleChange}
              placeholder="e.g., John"
              className={inputClass("firstName")}
            />
            {errorText("firstName")}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Last Name
            </label>
            <input
              name="lastName"
              value={form.lastName}
              onChange={handleChange}
              placeholder="e.g., Doe"
              className={inputClass("lastName")}
            />
            {errorText("lastName")}
          </div>
        </div>

        {/* ADDRESS */}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Address
          </label>
          <input
            name="address"
            value={form.address}
            onChange={handleChange}
            placeholder="Enter full address"
            className={inputClass("address")}
          />
          {errorText("address")}
        </div>

        {/* STATE */}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            State
          </label>
          <input
            name="stateName"
            value={form.stateName}
            onChange={handleChange}
            placeholder="e.g., Maryland"
            className={inputClass("stateName")}
          />
          {errorText("stateName")}
        </div>

        {/* DOB + SEX */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Date of Birth
            </label>
            <input
              name="dateOfBirth"
              type="date"
              value={form.dateOfBirth}
              onChange={handleChange}
              className={inputClass("dateOfBirth")}
            />
            {errorText("dateOfBirth")}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Sex
            </label>
            <input
              name="sex"
              value={form.sex}
              onChange={handleChange}
              placeholder="M / F"
              className={inputClass("sex")}
            />
            {errorText("sex")}
          </div>
        </div>

        {/* PASSPORT + LICENSE */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Passport Number
            </label>
            <input
              name="passportNumber"
              value={form.passportNumber}
              onChange={handleChange}
              placeholder="Passport No."
              className={inputClass("passportNumber")}
            />
            {errorText("passportNumber")}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              License Number
            </label>
            <input
              name="licenseNumber"
              value={form.licenseNumber}
              onChange={handleChange}
              placeholder="License No."
              className={inputClass("licenseNumber")}
            />
            {errorText("licenseNumber")}
          </div>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            className="w-full bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700 transition"
          >
            Save Registration
          </button>
        </div>

      </form>
    </div>
  );
};

export default RegistrationForm;
