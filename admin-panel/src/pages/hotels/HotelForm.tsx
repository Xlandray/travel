import { Create, Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Form, Input, InputNumber, Switch } from "antd";

type HotelFormValues = {
  name: string;
  slug?: string;
  city: string;
  address?: string;
  phone?: string;
  star_rating?: number;
  description?: string;
  image_url?: string;
  is_active?: boolean;
};

export function HotelForm({ mode }: { mode: "create" | "edit" }) {
  const { formProps, saveButtonProps, form } = useForm<BaseRecord, HttpError, HotelFormValues>();

  const content = (
    <Form<HotelFormValues> {...formProps} layout="vertical">
      <Form.Item
        label="Otel Adı"
        name="name"
        rules={[{ required: true, message: "Lütfen otel adını giriniz." }]}
      >
        <Input placeholder="Örn: Cave Hotel Kapadokya" maxLength={255} />
      </Form.Item>

      <Form.Item
        label="Şehir"
        name="city"
        rules={[{ required: true, message: "Lütfen şehri giriniz." }]}
      >
        <Input placeholder="Örn: Ürgüp" maxLength={100} />
      </Form.Item>

      <Form.Item label="Slug" name="slug" tooltip="Boş bırakılırsa otel adından otomatik üretilir">
        <Input placeholder="Örn: cave-hotel-kapadokya" maxLength={255} />
      </Form.Item>

      <div style={{ display: "flex", gap: "16px" }}>
        <Form.Item label="Yıldız" name="star_rating" style={{ flex: 1 }}>
          <InputNumber min={1} max={5} style={{ width: "100%" }} placeholder="5" />
        </Form.Item>

        <Form.Item label="Telefon" name="phone" style={{ flex: 2 }}>
          <Input placeholder="Örn: +90 384 341 00 00" maxLength={50} />
        </Form.Item>
      </div>

      <Form.Item label="Adres" name="address">
        <Input.TextArea rows={2} placeholder="Otel adresi..." maxLength={500} />
      </Form.Item>

      <Form.Item label="Açıklama" name="description">
        <Input.TextArea rows={3} placeholder="Otel hakkında kısa bilgi..." />
      </Form.Item>

      <Form.Item label="Görsel URL" name="image_url" tooltip="Otel görseli linki (opsiyonel)">
        <Input placeholder="https://..." maxLength={500} />
      </Form.Item>

      <Form.Item label="Aktif mi?" name="is_active" valuePropName="checked" initialValue={true}>
        <Switch />
      </Form.Item>
    </Form>
  );

  return mode === "create" ? (
    <Create saveButtonProps={saveButtonProps} title="Yeni Otel Oluştur">
      {content}
    </Create>
  ) : (
    <Edit
      saveButtonProps={{ ...saveButtonProps, onClick: () => form.submit() }}
      title="Otel Düzenle"
    >
      {content}
    </Edit>
  );
}
