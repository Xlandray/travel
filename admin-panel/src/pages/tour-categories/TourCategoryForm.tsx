import { Create, Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Form, Input, Switch } from "antd";

type TourCategoryFormValues = {
  name: string;
  slug?: string;
  is_active?: boolean;
};

export function TourCategoryForm({ mode }: { mode: "create" | "edit" }) {
  const { formProps, saveButtonProps, form } = useForm<
    BaseRecord,
    HttpError,
    TourCategoryFormValues
  >();

  const content = (
    <Form<TourCategoryFormValues> {...formProps} layout="vertical">
      <Form.Item
        label="Kategori Adı"
        name="name"
        rules={[{ required: true, message: "Lütfen kategori adını giriniz." }]}
      >
        <Input placeholder="Örn: Günübirlik Turlar" />
      </Form.Item>

      <Form.Item
        label="Slug (URL)"
        name="slug"
        tooltip="Boş bırakılırsa kategori adından otomatik üretilir."
      >
        <Input placeholder="Örn: gunubirlik-turlar" />
      </Form.Item>

      <Form.Item label="Aktif mi?" name="is_active" valuePropName="checked" initialValue={true}>
        <Switch />
      </Form.Item>
    </Form>
  );

  return mode === "create" ? (
    <Create saveButtonProps={saveButtonProps} title="Yeni Tur Kategorisi Oluştur">
      {content}
    </Create>
  ) : (
    <Edit saveButtonProps={{ ...saveButtonProps, onClick: () => form.submit() }} title="Kategori Düzenle">
      {content}
    </Edit>
  );
}
