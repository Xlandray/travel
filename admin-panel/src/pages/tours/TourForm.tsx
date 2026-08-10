import { Create, Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Form, Input, InputNumber, Select, Upload, Switch, message } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import type { UploadChangeParam, UploadFile } from "antd/es/upload";

import { axiosInstance } from "../../providers/axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8081/api/v1";

type CategoryOption = {
  id: string;
  name: string;
};

type TourFormValues = {
  title: string;
  slug?: string;
  description?: string;
  days: number;
  nights: number;
  price: number;
  category_id?: string;
  image_url?: string | UploadFile[];
  is_active: boolean;
};

type TourFormProps = {
  mode: "create" | "edit";
};

// Görsel yükleme: Upload fileList'ini form değeri olarak tutar.
function normFile(e: UploadChangeParam<UploadFile> | UploadFile[]) {
  if (Array.isArray(e)) {
    return e;
  }
  return e?.fileList;
}

// Form değerini Upload fileList'ine dönüştürür (edit modunda string gelebilir).
function fileListFromValue(v: unknown): UploadFile[] {
  if (Array.isArray(v)) {
    return v as UploadFile[];
  }
  if (typeof v === "string" && v) {
    return [{ uid: "-1", name: "mevcut-gorsel", status: "done", url: v }];
  }
  return [];
}

function urlFromFileList(list: UploadFile[] | undefined): string | undefined {
  const done = (list ?? []).filter(
    (f) => f.status === "done" || f.url,
  );
  const last = done.at(-1);
  return last?.response?.url || last?.response?.path || last?.url;
}

export function TourForm({ mode }: TourFormProps) {
  const { formProps, saveButtonProps, form } = useForm<
    BaseRecord,
    HttpError,
    TourFormValues
  >();
  const [categories, setCategories] = useState<CategoryOption[]>([]);

  useEffect(() => {
    axiosInstance
      .get("tour-categories")
      .then((res) => setCategories((res.data ?? []) as CategoryOption[]))
      .catch(() => setCategories([]));
  }, []);

  // Submit: image_url (fileList) -> url string olarak gönderilir
  const onFinish = (values: TourFormValues) => {
    const { image_url: imgList, ...rest } = values;
    const image_url = urlFromFileList(imgList as UploadFile[] | undefined);
    formProps.onFinish?.({ ...rest, image_url });
  };

  const content = (
    <Form<TourFormValues> {...formProps} layout="vertical" onFinish={onFinish}>
      <Form.Item
        label="Tur Adı"
        name="title"
        rules={[{ required: true, message: "Lütfen tur adını giriniz." }]}
      >
        <Input placeholder="Örn: Kapadokya ve Balon Turu" />
      </Form.Item>

      <Form.Item label="Slug (URL)" name="slug" tooltip="Boş bırakılırsa tur adından otomatik üretilir.">
        <Input placeholder="Örn: kapadokya-vip-balon-turu" />
      </Form.Item>

      <Form.Item label="Kategori" name="category_id">
        <Select allowClear placeholder="Kategori seçin">
          {categories.map((c) => (
            <Select.Option key={c.id} value={c.id}>
              {c.name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item label="Açıklama" name="description">
        <Input.TextArea rows={4} placeholder="Tur hakkında detaylı bilgi..." />
      </Form.Item>

      <div style={{ display: "flex", gap: "16px" }}>
        <Form.Item label="Başlangıç Fiyatı (₺)" name="price" style={{ flex: 1 }}>
          <InputNumber style={{ width: "100%" }} min={0} placeholder="6500" />
        </Form.Item>

        <Form.Item
          label="Gün Sayısı"
          name="days"
          initialValue={1}
          style={{ flex: 1 }}
          rules={[{ required: true, message: "Gün sayısı zorunludur." }]}
        >
          <InputNumber min={1} style={{ width: "100%" }} />
        </Form.Item>

        <Form.Item
          label="Gece Sayısı"
          name="nights"
          initialValue={0}
          style={{ flex: 1 }}
          rules={[{ required: true, message: "Gece sayısı zorunludur." }]}
        >
          <InputNumber min={0} style={{ width: "100%" }} />
        </Form.Item>
      </div>

      <Form.Item
        label="Kapak Görseli"
        name="image_url"
        valuePropName="fileList"
        getValueFromEvent={normFile}
        getValueProps={(value) => ({ fileList: fileListFromValue(value) })}
      >
        <Upload.Dragger
          name="file"
          action={`${API_URL}/upload`}
          listType="picture"
          maxCount={1}
          onChange={({ file }) => {
            if (file.status === "error") {
              message.error(`${file.name} yüklenirken hata oluştu.`);
            }
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Görseli buraya sürükleyin veya tıklayarak seçin</p>
          <p className="ant-upload-hint">Yüksek çözünürlüklü JPEG, PNG veya WEBP dosyaları desteklenir.</p>
        </Upload.Dragger>
      </Form.Item>

      <Form.Item label="Aktif mi?" name="is_active" valuePropName="checked" initialValue={true}>
        <Switch />
      </Form.Item>
    </Form>
  );

  return mode === "create" ? (
    <Create saveButtonProps={saveButtonProps} title="Yeni Tur Oluştur">
      {content}
    </Create>
  ) : (
    <Edit
      saveButtonProps={{ ...saveButtonProps, onClick: () => form.submit() }}
      title="Turu Düzenle"
    >
      {content}
    </Edit>
  );
}