import { Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Button, Form, Input, Popconfirm, Switch, Typography, message } from "antd";
import { useState } from "react";
import { useParams } from "react-router";

import { axiosInstance } from "../../providers/axios";

type UserFormValues = {
  email?: string;
  full_name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
};

export function UserForm() {
  const { formProps, saveButtonProps, form } = useForm<BaseRecord, HttpError, UserFormValues>();
  const { id } = useParams<{ id: string }>();
  const [revoking, setRevoking] = useState(false);

  /**
   * Access tokens cannot be taken back one at a time — the server keeps no
   * record of them — so this bumps the account's token version, which ends
   * every session it has at once. Suspending the account would also do it, but
   * it locks the person out of their own; this leaves them able to log in
   * again while whoever holds a stolen copy cannot.
   */
  const revokeSessions = async () => {
    if (!id) return;
    setRevoking(true);
    try {
      await axiosInstance.post(`/admin/users/${id}/revoke-sessions`);
      message.success("Kullanıcının tüm oturumları sonlandırıldı.");
    } catch {
      message.error("Oturumlar sonlandırılamadı.");
    } finally {
      setRevoking(false);
    }
  };

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

      <Form.Item label="Oturum Güvenliği">
        <Popconfirm
          title="Tüm oturumlar sonlandırılsın mı?"
          description="Kullanıcı açık olduğu her cihazdan çıkış yapmış olur ve yeniden giriş yapması gerekir. Hesabı kapatılmaz."
          okText="Sonlandır"
          cancelText="Vazgeç"
          okButtonProps={{ danger: true }}
          onConfirm={revokeSessions}
        >
          <Button danger loading={revoking} disabled={!id}>
            Tüm Oturumları Sonlandır
          </Button>
        </Popconfirm>
        <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
          Kullanıcının erişim anahtarı sızdıysa kullanın. Anahtarlar sunucuda saklanmadığı için tek
          tek geri alınamaz; hepsi birden geçersiz kılınır.
        </Typography.Paragraph>
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
