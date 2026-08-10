import { Create, Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Button, Form, Input, Space } from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { useEffect } from "react";
import type { JsonValue } from "./JsonValueInput";
import { JsonValueInput } from "./JsonValueInput";

type Entry = {
  key: string;
  value?: JsonValue;
};

type SettingsFormValues = {
  key?: string;
  entries?: Entry[];
  description?: string;
};

type SettingsFormProps = {
  mode: "create" | "edit";
};

function toEntries(value: Record<string, JsonValue> | undefined): Entry[] {
  return Object.entries(value ?? {}).map(([k, v]) => ({ key: k, value: v }));
}

function toDict(entries: Entry[] | undefined): Record<string, JsonValue> {
  const dict: Record<string, JsonValue> = {};
  (entries ?? []).forEach(({ key, value }) => {
    if (key.trim()) dict[key.trim()] = value ?? "";
  });
  return dict;
}

export function SettingsForm({ mode }: SettingsFormProps) {
  const { formProps, saveButtonProps, form, query } = useForm<
    BaseRecord,
    HttpError,
    SettingsFormValues
  >();

  useEffect(() => {
    const data = query?.data?.data as { value?: Record<string, JsonValue> } | undefined;
    if (mode === "edit" && data) {
      form.setFieldsValue({ entries: toEntries(data.value) });
    }
  }, [form, mode, query?.data]);

  const onFinish = (values: SettingsFormValues) => {
    const { entries, ...rest } = values;
    formProps.onFinish?.({ ...rest, value: toDict(entries) } as SettingsFormValues);
  };

  const content = (
    <Form<SettingsFormValues> {...formProps} layout="vertical" onFinish={onFinish}>
      {mode === "create" ? (
        <Form.Item
          label="Anahtar (Key)"
          name="key"
          rules={[
            { required: true, message: "Lütfen anahtar giriniz." },
            {
              pattern: /^[a-z][a-z0-9_]*$/,
              message: "Küçük harfle başlamalı; yalnızca küçük harf, rakam ve alt çizgi kullanın.",
            },
          ]}
        >
          <Input placeholder="Örn: site_baslik" maxLength={100} />
        </Form.Item>
      ) : null}

      <Form.Item
        label="Değerler"
        tooltip="Ayara bağlı anahtar-değer çiftleri. Değer türünü seçin (metin, sayı, JSON nesne/liste vb.)."
      >
        <Form.List name="entries">
          {(fields, { add, remove }) => (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {fields.map((field) => (
                <Space key={field.key} align="start">
                  <Form.Item
                    name={[field.name, "key"]}
                    rules={[{ required: true, message: "Anahtar zorunludur." }]}
                    style={{ marginBottom: 0, minWidth: 200 }}
                  >
                    <Input placeholder="Anahtar" />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, "value"]}
                    valuePropName="value"
                    style={{ marginBottom: 0, flex: 1, minWidth: 320 }}
                  >
                    <JsonValueInput />
                  </Form.Item>
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => remove(field.name)}
                  />
                </Space>
              ))}
              <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ key: "" })}>
                Değer Ekle
              </Button>
            </div>
          )}
        </Form.List>
      </Form.Item>

      <Form.Item label="Açıklama" name="description">
        <Input.TextArea
          rows={2}
          placeholder="Bu ayarın ne işe yaradığına dair kısa not..."
          maxLength={255}
        />
      </Form.Item>
    </Form>
  );

  return mode === "create" ? (
    <Create saveButtonProps={saveButtonProps} title="Yeni Ayar Oluştur">
      {content}
    </Create>
  ) : (
    <Edit
      saveButtonProps={{ ...saveButtonProps, onClick: () => form.submit() }}
      title="Ayar Düzenle"
    >
      {content}
    </Edit>
  );
}
