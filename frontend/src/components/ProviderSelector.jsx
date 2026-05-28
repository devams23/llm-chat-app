import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";

export default function ProviderSelector({ onProviderChange }) {
  const [providers, setProviders] = useState({});
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  
  useEffect(() => {
    loadProviders();
  }, []);
  
  const loadProviders = async () => {
    try {
      const data = await chatAPI.getAvailableProviders();
      const safeData = data && typeof data === "object" ? data : {};
      setProviders(safeData);

      const providerKeys = Object.keys(safeData);
      const defaultProvider = providerKeys[0] || "";
      const models = safeData[defaultProvider] || [];
      const defaultModel = models[0] || "";

      setSelectedProvider(defaultProvider);
      setSelectedModel(defaultModel);
      if (defaultProvider && defaultModel) {
        onProviderChange?.(defaultProvider, defaultModel);
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };
  
  const handleProviderChange = (e) => {
    const newProvider = e.target.value;
    setSelectedProvider(newProvider);
    
    // Auto-select first model of new provider
    const models = providers[newProvider] || [];
    const nextModel = models[0] || "";
    setSelectedModel(nextModel);
    
    onProviderChange?.(newProvider, nextModel);
  };
  
  const handleModelChange = (e) => {
    const newModel = e.target.value;
    setSelectedModel(newModel);
    onProviderChange?.(selectedProvider, newModel);
  };
  
  return (
    <div className="provider-selector">
      <label>
        Provider:
        <select value={selectedProvider} onChange={handleProviderChange}>
          {Object.keys(providers).map(provider => (
            <option key={provider} value={provider}>
              {provider.charAt(0).toUpperCase() + provider.slice(1)}
            </option>
          ))}
        </select>
      </label>
      
      <label>
        Model:
        <select value={selectedModel} onChange={handleModelChange}>
          {(providers[selectedProvider] || []).map(model => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}