import { useCreate, useOne, useUpdate } from "@refinedev/core";
import { Create, Edit } from "@refinedev/antd";
import { Form, Input, message } from "antd";
import { useEffect } from "react";
import { useNavigate, useParams } from "react-router";

type JsonResourceFormPageProps = {
  resource: string;
  title: string;
  mode: "create" | "edit";
};

type FormValues = { payload: string };

const writableFields: Record<string, Record<JsonResourceFormPageProps["mode"], string[]>> = {
  "admin/contents": {
    create: ["title", "slug", "body", "is_published"],
    edit: ["title", "slug", "body", "is_published"],
  },
  "admin/settings": {
    create: ["key", "value", "description"],
    edit: ["value", "description"],
  },
  "admin/users": {
    create: [],
    edit: ["full_name", "is_active", "is_superuser"],
  },
  "tour-categories": {
    create: ["name", "slug", "is_active"],
    edit: ["name", "slug", "is_active"],
  },
};

function selectWritableFields(
  resource: string,
  mode: JsonResourceFormPageProps["mode"],
  value: Record<string, unknown>,
): Record<string, unknown> {
  return Object.fromEntries(
    (writableFields[resource]?.[mode] ?? []).flatMap((field) =>
      field in value ? [[field, value[field]]] : [],
    ),
  );
}

function parsePayload(payload: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(payload);
    if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
      throw new Error("Payload must be an object.");
    }
    return parsed as Record<string, unknown>;
  } catch {
    message.error("Geçerli bir JSON nesnesi girin.");
    return null;
  }
}

export function JsonResourceFormPage({ resource, title, mode }: JsonResourceFormPageProps) {
  const navigate = useNavigate();
  const { id } = useParams();
  const [form] = Form.useForm<FormValues>();
  const { mutate: createRecord, mutation } = useCreate();
  const { mutate: updateRecord, mutation: updateMutation } = useUpdate();
  const { query } = useOne<Record<string, unknown>>({
    resource,
    id: id ?? "",
    queryOptions: { enabled: mode === "edit" && Boolean(id) },
  });
  const listPath = `/${resource.split("/").at(-1)}`;

  useEffect(() => {
    if (query.data?.data) {
      const writableData = selectWritableFields(resource, mode, query.data.data);
      form.setFieldValue("payload", JSON.stringify(writableData, null, 2));
    }
  }, [form, mode, query.data, resource]);

  const submit = ({ payload }: FormValues) => {
    const values = parsePayload(payload);
    if (!values) return;
    const writableValues = selectWritableFields(resource, mode, values);

    if (mode === "create") {
      createRecord(
        { resource, values: writableValues },
        { onSuccess: () => navigate(listPath) },
      );
      return;
    }
    updateRecord(
      { resource, id: id ?? "", values: writableValues },
      { onSuccess: () => navigate(listPath) },
    );
  };

  const content = (
    <Form<FormValues> form={form} layout="vertical" onFinish={submit}>
      <Form.Item
        label="JSON payload"
        name="payload"
        rules={[{ required: true, message: "JSON payload zorunludur." }]}
      >
        <Input.TextArea autoSize={{ minRows: 14 }} spellCheck={false} />
      </Form.Item>
    </Form>
  );

  return mode === "create" ? (
    <Create title={title} saveButtonProps={{ loading: mutation.isPending, onClick: form.submit }}>
      {content}
    </Create>
  ) : (
    <Edit
      title={title}
      saveButtonProps={{ loading: updateMutation.isPending, onClick: form.submit }}
    >
      {content}
    </Edit>
  );
}
