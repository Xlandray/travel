import { Create, Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import {
  Button,
  Divider,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Upload,
  Switch,
  message,
} from "antd";
import { DeleteOutlined, InboxOutlined, PlusOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import type { UploadChangeParam, UploadFile } from "antd/es/upload";

import { axiosInstance } from "../../providers/axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8081/api/v1";

type CategoryOption = {
  id: string;
  name: string;
};

type HotelOption = {
  id: string;
  name: string;
  city: string;
};

type BoardingPointOption = {
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
  images?: UploadFile[];
  hotels?: { hotel_id: string; night_order: number }[];
  route_stops?: {
    day_number: number;
    sort_order: number;
    title: string;
    description?: string;
    boarding_point_ids?: string[];
  }[];
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

// Form değerini Upload fileList'ine dönüştürür (edit modunda mevcut galeri dizisi gelebilir).
function fileListFromValue(v: unknown): UploadFile[] {
  if (Array.isArray(v)) {
    return v.map((img, i) => {
      if (img?.uid) return img as UploadFile;
      const url = img?.url ?? img;
      return { uid: String(i), name: `gorsel-${i + 1}`, status: "done", url: String(url) };
    });
  }
  return [];
}

function urlFromFile(file: UploadFile): string | undefined {
  return file?.response?.url || file?.response?.path || file?.url;
}

// Upload fileList'ini backend `images` dizisine (url + sort_order) çevirir.
function imagesFromFileList(list: UploadFile[] | undefined): { url: string; sort_order: number }[] {
  return (list ?? [])
    .filter((f) => f.status === "done" || f.url || f.response)
    .map((f, i) => ({ url: String(urlFromFile(f) ?? ""), sort_order: i }))
    .filter((img) => img.url);
}

export function TourForm({ mode }: TourFormProps) {
  const { formProps, saveButtonProps, form } = useForm<BaseRecord, HttpError, TourFormValues>();
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [hotels, setHotels] = useState<HotelOption[]>([]);
  const [boardingPoints, setBoardingPoints] = useState<BoardingPointOption[]>([]);

  useEffect(() => {
    axiosInstance
      .get("tour-categories")
      .then((res) => setCategories((res.data ?? []) as CategoryOption[]))
      .catch(() => setCategories([]));
    axiosInstance
      .get("hotels")
      .then((res) => setHotels((res.data ?? []) as HotelOption[]))
      .catch(() => setHotels([]));
    axiosInstance
      .get("tours/boarding-points")
      .then((res) => setBoardingPoints((res.data ?? []) as BoardingPointOption[]))
      .catch(() => setBoardingPoints([]));
  }, []);

  // Submit: images (fileList) -> {image_url, images[]} olarak gönderilir.
  const onFinish = (values: TourFormValues) => {
    const { images, hotels, route_stops, ...rest } = values;
    const imageList = imagesFromFileList(images as UploadFile[] | undefined);
    const hotelList = (hotels ?? [])
      .filter((h) => h.hotel_id)
      .map((h, i) => ({ hotel_id: h.hotel_id, night_order: h.night_order || i + 1 }));
    const routeStopList = (route_stops ?? [])
      .filter((r) => r.title)
      .map((r, i) => ({
        day_number: r.day_number || i + 1,
        sort_order: r.sort_order ?? i,
        title: r.title,
        description: r.description ?? "",
        boarding_point_ids: r.boarding_point_ids ?? [],
      }));
    formProps.onFinish?.({
      ...rest,
      image_url: imageList[0]?.url ?? "",
      images: imageList,
      hotels: hotelList,
      route_stops: routeStopList,
    } as unknown as TourFormValues);
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

      <Form.Item
        label="Slug (URL)"
        name="slug"
        tooltip="Boş bırakılırsa tur adından otomatik üretilir."
      >
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
        label="Tur Görselleri"
        name="images"
        valuePropName="fileList"
        getValueFromEvent={normFile}
        getValueProps={(value) => ({ fileList: fileListFromValue(value) })}
        tooltip="Birden fazla görsel ekleyebilirsiniz. İlk görsel kapak görseli olarak kullanılır."
      >
        <Upload.Dragger
          name="file"
          action={`${API_URL}/upload`}
          listType="picture"
          multiple
          accept="image/jpeg,image/png,image/webp,image/gif"
          headers={{ Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}` }}
          beforeUpload={(file) => {
            const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
            if (!allowed.includes(file.type)) {
              message.error(`${file.name}: yalnızca JPG, PNG, WEBP veya GIF yüklenebilir.`);
              return Upload.LIST_IGNORE;
            }
            if (file.size > 10 * 1024 * 1024) {
              message.error(`${file.name}: görsel 10MB sınırını aşıyor.`);
              return Upload.LIST_IGNORE;
            }
            return true;
          }}
          onChange={({ file }) => {
            if (file.status === "error") {
              const detail =
                (file.response as { detail?: string } | null)?.detail ??
                "Sunucuya bağlanılamadı veya istek tamamlanamadı. Görselin JPG/PNG/WEBP/GIF ve ≤10MB olduğundan emin olun.";
              message.error(`${file.name}: ${detail}`);
            }
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Görselleri buraya sürükleyin veya tıklayarak seçin</p>
          <p className="ant-upload-hint">
            Yüksek çözünürlüklü JPEG, PNG veya WEBP dosyaları desteklenir. Birden fazla dosya
            seçilebilir.
          </p>
        </Upload.Dragger>
      </Form.Item>

      <Divider orientation="left">Oteller</Divider>
      <Form.Item
        label="Konaklama Otelleri"
        tooltip="Turda kullanılacak oteller; gece sırası hangi gece hangi otel olduğunu belirtir."
      >
        <Form.List name="hotels">
          {(fields, { add, remove }) => (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {fields.map((field) => (
                <Space key={field.key} align="start">
                  <Form.Item
                    name={[field.name, "hotel_id"]}
                    rules={[{ required: true, message: "Otel seçin." }]}
                    style={{ marginBottom: 0, minWidth: 260 }}
                  >
                    <Select
                      showSearch
                      optionFilterProp="label"
                      placeholder="Otel seçin"
                      options={hotels.map((h) => ({
                        value: h.id,
                        label: `${h.name} (${h.city})`,
                      }))}
                    />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, "night_order"]}
                    style={{ marginBottom: 0 }}
                    tooltip="1 = ilk gece"
                  >
                    <InputNumber min={1} placeholder="Gece" style={{ width: 100 }} />
                  </Form.Item>
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => remove(field.name)}
                  />
                </Space>
              ))}
              <Button
                type="dashed"
                icon={<PlusOutlined />}
                onClick={() => add({ night_order: fields.length + 1 })}
              >
                Otel Ekle
              </Button>
            </div>
          )}
        </Form.List>
      </Form.Item>

      <Divider orientation="left">Rota / Gün Programı</Divider>
      <Form.Item
        label="Günlük Program"
        tooltip="Her gün için başlık, açıklama ve o güne ait biniş durakları."
      >
        <Form.List name="route_stops">
          {(fields, { add, remove }) => (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {fields.map((field) => (
                <div
                  key={field.key}
                  style={{
                    border: "1px solid #d9d9d9",
                    borderRadius: 8,
                    padding: 12,
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <Form.Item
                      name={[field.name, "day_number"]}
                      style={{ marginBottom: 0 }}
                      rules={[{ required: true, message: "Gün no girin." }]}
                    >
                      <InputNumber min={1} placeholder="Gün" style={{ width: 80 }} />
                    </Form.Item>
                    <Form.Item
                      name={[field.name, "title"]}
                      style={{ marginBottom: 0, flex: 1 }}
                      rules={[{ required: true, message: "Başlık zorunludur." }]}
                    >
                      <Input placeholder="Gün başlığı (örn: Çorlu'dan hareket)" />
                    </Form.Item>
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => remove(field.name)}
                    />
                  </div>
                  <Form.Item name={[field.name, "description"]} style={{ marginBottom: 0 }}>
                    <Input.TextArea rows={2} placeholder="Günün detaylı anlatımı..." />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, "boarding_point_ids"]}
                    style={{ marginBottom: 0 }}
                    tooltip="Bu güne ait biniş durakları."
                  >
                    <Select
                      mode="multiple"
                      allowClear
                      placeholder="Biniş durakları seçin"
                      options={boardingPoints.map((bp) => ({
                        value: bp.id,
                        label: bp.name,
                      }))}
                    />
                  </Form.Item>
                </div>
              ))}
              <Button
                type="dashed"
                icon={<PlusOutlined />}
                onClick={() =>
                  add({
                    day_number: fields.length + 1,
                    sort_order: fields.length,
                    boarding_point_ids: [],
                  })
                }
              >
                Gün Ekle
              </Button>
            </div>
          )}
        </Form.List>
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
