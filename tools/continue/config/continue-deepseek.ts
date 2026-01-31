import { Config } from "@continuedev/server";

export function modifyConfig(config: Config): Config {
  // 配置 DeepSeek 模型
  config.models = [
    {
      title: "DeepSeek Coder",
      provider: "openai",
      model: "deepseek-coder",
      apiKey: process.env.DEEPSEEK_API_KEY || "",
      apiBase: "https://api.deepseek.com",
      contextLength: 16384,
    },
    {
      title: "DeepSeek Chat",
      provider: "openai",
      model: "deepseek-chat",
      apiKey: process.env.DEEPSEEK_API_KEY || "",
      apiBase: "https://api.deepseek.com",
      contextLength: 32768,
    },
    {
      title: "GPT-4",
      provider: "openai",
      model: "gpt-4",
      apiKey: process.env.OPENAI_API_KEY || "",
    },
  ];
  
  // 设置默认模型
  config.defaultModel = "DeepSeek Coder";
  
  // 配置 Tab 自动完成模型
  config.tabAutocompleteModel = {
    title: "DeepSeek Coder",
    provider: "openai",
    model: "deepseek-coder",
    apiKey: process.env.DEEPSEEK_API_KEY || "",
    apiBase: "https://api.deepseek.com",
  };
  
  // 配置嵌入模型
  config.embeddingsProvider = {
    provider: "openai",
    model: "text-embedding-3-small",
    apiKey: process.env.OPENAI_API_KEY || "",
  };
  
  // 其他配置
  config.allowAnonymousTelemetry = false;
  config.experimental = {
    disableIndexing: true,
  };
  
  return config;
}