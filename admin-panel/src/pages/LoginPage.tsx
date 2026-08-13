import { useLogin } from "@refinedev/core";
import { Button, Card, Form, Input, Typography } from "antd";

type LoginFormValues = { email: string; password: string };

export function LoginPage() {
  const { mutate: login, isPending } = useLogin<LoginFormValues>();

  return (
    <main
      style={{ display: "grid", minHeight: "100vh", placeItems: "center", background: "#f8fafc" }}
    >
      <Card style={{ width: 400, borderRadius: 12, boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div
            style={{
              display: "inline-flex",
              gap: 4,
              borderRadius: 6,
              overflow: "hidden",
              marginBottom: 12,
            }}
          >
            <span
              style={{
                background: "#961358",
                color: "#fff",
                padding: "6px 12px",
                fontWeight: "bold",
                fontSize: 14,
              }}
            >
              UPDATE
            </span>
            <span
              style={{
                background: "#00A699",
                color: "#fff",
                padding: "6px 12px",
                fontWeight: "bold",
                fontSize: 14,
              }}
            >
              ARMONİTEX
            </span>
          </div>
          <Typography.Title level={3} style={{ margin: 0, color: "#0a2540" }}>
            Yönetim Paneli Girişi
          </Typography.Title>
        </div>
        <Form<LoginFormValues> layout="vertical" onFinish={(values) => login(values)}>
          <Form.Item label="E-posta" name="email" rules={[{ required: true, type: "email" }]}>
            <Input autoComplete="email" />
          </Form.Item>
          <Form.Item label="Parola" name="password" rules={[{ required: true }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Button block htmlType="submit" loading={isPending} type="primary">
            Giriş yap
          </Button>
        </Form>
      </Card>
    </main>
  );
}
