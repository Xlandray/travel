import { Edit, useForm } from "@refinedev/antd";
import type { BaseRecord, HttpError } from "@refinedev/core";
import { Form, InputNumber, Select, DatePicker, Switch, Input } from "antd";
import { useEffect, useState } from "react";
import dayjs, { type Dayjs } from "dayjs";

import { axiosInstance } from "../../providers/axios";

interface TourOption {
  id: string;
  title: string;
}

interface FormValues {
  tour_id: string;
  dateRange?: [Dayjs, Dayjs];
  price: number;
  total_quota: number;
  available_seats: number;
  is_active?: boolean;
  start_date?: string;
  end_date?: string;
}

export const TourDepartureEdit = () => {
  const { formProps, saveButtonProps, form } = useForm<
    BaseRecord,
    HttpError,
    FormValues
  >();
  const [tours, setTours] = useState<TourOption[]>([]);

  useEffect(() => {
    axiosInstance
      .get("tours")
      .then((res) => setTours((res.data ?? []) as TourOption[]))
      .catch(() => setTours([]));
  }, []);

  // Edit modunda geri yüklenen tarihleri RangePicker formatına çevir
  const onFieldsChange = () => {
    const values = form.getFieldsValue(true) as Partial<FormValues>;
    const start = values?.start_date;
    const end = values?.end_date;
    if (start && end && !values?.dateRange) {
      form.setFieldValue("dateRange", [dayjs(start as string), dayjs(end as string)]);
    }
  };

  const handleOnFinish = (values: FormValues) => {
    const { tour_id, dateRange, price, total_quota, available_seats, is_active } = values;
    const startDate = dateRange?.[0]?.format("YYYY-MM-DD");
    const endDate = dateRange?.[1]?.format("YYYY-MM-DD");

    if (!startDate || !endDate) {
      return;
    }

    const submitData = {
      tour_id,
      start_date: startDate,
      end_date: endDate,
      price,
      total_quota,
      available_seats,
      is_active: is_active ?? true,
    };

    formProps.onFinish?.(submitData);
  };

  return (
    <Edit
      saveButtonProps={{
        ...saveButtonProps,
        onClick: () => form.submit(),
      }}
      title="Seferi Düzenle"
    >
      <Form {...formProps} layout="vertical" onFinish={handleOnFinish} onFieldsChange={onFieldsChange}>
        <Form.Item
          label="Tur Seçin"
          name="tour_id"
          rules={[{ required: true, message: "Lütfen bir tur seçin." }]}
        >
          <Select allowClear placeholder="Seferin ait olduğu turu seçin">
            {tours.map((t) => (
              <Select.Option key={t.id} value={t.id}>
                {t.title}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="Sefer Tarih Aralığı (Başlangıç - Bitiş)"
          name="dateRange"
          rules={[{ required: true, message: "Lütfen tarih aralığını seçin." }]}
        >
          <DatePicker.RangePicker style={{ width: "100%" }} format="YYYY-MM-DD" />
        </Form.Item>

        <Form.Item label="Başlangıç Tarihi" name="start_date" hidden>
          <Input style={{ display: "none" }} />
        </Form.Item>
        <Form.Item label="Bitiş Tarihi" name="end_date" hidden>
          <Input style={{ display: "none" }} />
        </Form.Item>

        <div style={{ display: "flex", gap: "16px" }}>
          <Form.Item
            label="Kişi Başı Fiyat (₺)"
            name="price"
            style={{ flex: 1 }}
            rules={[{ required: true, message: "Fiyat giriniz." }]}
          >
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              placeholder="6500"
              formatter={(value: number | undefined) =>
                `₺ ${value ?? 0}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",")
              }
              parser={(value: string | undefined) => Number(value?.replace(/₺\s?|(,*)/g, "")) || 0}
            />
          </Form.Item>

          <Form.Item
            label="Otobüs Kapasitesi (Toplam Stok)"
            name="total_quota"
            style={{ flex: 1 }}
            rules={[{ required: true, message: "Kapasite giriniz." }]}
          >
            <InputNumber style={{ width: "100%" }} min={1} placeholder="45" />
          </Form.Item>
        </div>

        <Form.Item
          label="Kalan Koltuk"
          name="available_seats"
          tooltip="Mevcut satılabilecek koltuk sayısı (stok)."
        >
          <InputNumber style={{ width: "100%" }} min={0} placeholder="45" />
        </Form.Item>

        <Form.Item label="Satışa Açık mı?" name="is_active" valuePropName="checked" initialValue={true}>
          <Switch />
        </Form.Item>
      </Form>
    </Edit>
  );
};