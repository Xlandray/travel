import { Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Form, Input, Switch } from "antd";

type UserFormValues = {
  email?: string;
  full_name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
};

export function UserForm() {
  const { formProps, saveButtonProps, form } = useForm<BaseRecord, HttpError, UserFormValues>();

  const content = (
    <Form<UserFormValues> {...formProps} layout="vertical">
      <Form.Item label="E-posta" name="email">
        <Input disabled placeholder="E-posta değiştirilemez." />
      </Form.Item>

      <Form.Item label="Ad Soyad" name="full_name" rules={[{ max: 150 }]}>
        <Input placeholder="Kullanıcının adı ve soyadı" maxLength={150} />
      </Form.Item>

      <Form.Item label="Aktif mi?" name="is_active" valuePropName="checked" initialValue={true}>
        <Switch />
      </Form.Item>

      <Form.Item
        label="Süper Admin"
        name="is_superuser"
        valuePropName="checked"
        initialValue={false}
      >
        <Switch />
      </Form.Item>
    </Form>
  );

  return (
    <Edit
      saveButtonProps={{ ...saveButtonProps, onClick: () => form.submit() }}
      title="Kullanıcı Düzenle"
    >
      {content}
    </Edit>
  );
}
