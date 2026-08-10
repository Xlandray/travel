import { Create, Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Form, Input, Switch } from "antd";

type ContentFormValues = {
  title: string;
  slug?: string;
  body?: string;
  is_published?: boolean;
};

export function ContentForm({ mode }: { mode: "create" | "edit" }) {
  const { formProps, saveButtonProps, form } = useForm<BaseRecord, HttpError, ContentFormValues>();

  const content = (
    <Form<ContentFormValues> {...formProps} layout="vertical">
      <Form.Item
        label="Başlık"
        name="title"
        rules={[{ required: true, message: "Lütfen içerik başlığını giriniz." }]}
      >
        <Input placeholder="Örn: Yeni Sezon Turları Başladı" />
      </Form.Item>

      <Form.Item
        label="Slug (URL)"
        name="slug"
        tooltip="Boş bırakılırsa başlıktan üretilmez; küçük harf ve tire kullanın."
      >
        <Input placeholder="Örn: yeni-sezon-turlari" />
      </Form.Item>

      <Form.Item
        label="İçerik"
        name="body"
        rules={[{ required: true, message: "Lütfen içerik giriniz." }]}
      >
        <Input.TextArea rows={10} placeholder="İçerik metni..." />
      </Form.Item>

      <Form.Item
        label="Yayınla"
        name="is_published"
        valuePropName="checked"
        initialValue={false}
      >
        <Switch />
      </Form.Item>
    </Form>
  );

  return mode === "create" ? (
    <Create saveButtonProps={saveButtonProps} title="Yeni İçerik Oluştur">
      {content}
    </Create>
  ) : (
    <Edit saveButtonProps={{ ...saveButtonProps, onClick: () => form.submit() }} title="İçerik Düzenle">
      {content}
    </Edit>
  );
}
