import { Input, InputNumber, Select, Switch } from "antd";
import { useState } from "react";

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | { [key: string]: JsonValue }
  | JsonValue[];

type JsonType = "string" | "number" | "boolean" | "object" | "array";

function detectType(value: JsonValue | undefined): JsonType {
  if (value === undefined || value === null) return "string";
  if (typeof value === "number") return "number";
  if (typeof value === "boolean") return "boolean";
  if (Array.isArray(value)) return "array";
  return "object";
}

function jsonify(value: JsonValue | undefined): string {
  return value === undefined ? "{}" : JSON.stringify(value, null, 2);
}

function parseJson(text: string): JsonValue | null {
  try {
    return JSON.parse(text) as JsonValue;
  } catch {
    return null;
  }
}

const LABELS: Record<JsonType, string> = {
  string: "Metin",
  number: "Sayı",
  boolean: "Doğru/Yanlış",
  object: "Nesne (JSON)",
  array: "Liste (JSON)",
};

type JsonValueInputProps = {
  value?: JsonValue;
  onChange?: (value: JsonValue) => void;
};

export function JsonValueInput({ value, onChange }: JsonValueInputProps) {
  const [type, setType] = useState<JsonType>(detectType(value));
  const [raw, setRaw] = useState<string>(() => {
    const v = value ?? undefined;
    return ["object", "array"].includes(detectType(v)) ? jsonify(v) : "";
  });

  const switchType = (next: JsonType) => {
    setType(next);
    if (next === "object") {
      setRaw("{}");
      onChange?.({});
    } else if (next === "array") {
      setRaw("[]");
      onChange?.([]);
    } else if (next === "boolean") {
      onChange?.(false);
    } else if (next === "number") {
      onChange?.(0);
    } else {
      setRaw("");
      onChange?.("");
    }
  };

  const emitRaw = (text: string) => {
    setRaw(text);
    const parsed = parseJson(text);
    if (parsed !== null) onChange?.(parsed);
  };

  let control: React.ReactNode;
  if (type === "string") {
    control = (
      <Input
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder="Metin değeri"
      />
    );
  } else if (type === "number") {
    control = (
      <InputNumber
        style={{ width: "100%" }}
        value={typeof value === "number" ? value : 0}
        onChange={(n) => onChange?.(n ?? 0)}
      />
    );
  } else if (type === "boolean") {
    control = (
      <Switch
        checked={value === true}
        onChange={(checked) => onChange?.(checked)}
      />
    );
  } else {
    const parsed = parseJson(raw);
    control = (
      <>
        <Input.TextArea
          rows={4}
          value={raw}
          spellCheck={false}
          onChange={(e) => emitRaw(e.target.value)}
          style={parsed === null ? { borderColor: "#ff4d4f" } : undefined}
        />
        {parsed === null ? (
          <div style={{ color: "#ff4d4f", fontSize: 12, marginTop: 4 }}>
            Geçerli bir JSON girin.
          </div>
        ) : null}
      </>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <Select<JsonType>
        value={type}
        onChange={switchType}
        style={{ width: 180 }}
        options={(Object.keys(LABELS) as JsonType[]).map((t) => ({
          value: t,
          label: LABELS[t],
        }))}
      />
      {control}
    </div>
  );
}
