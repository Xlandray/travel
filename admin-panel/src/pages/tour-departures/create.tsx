import { Create, useForm } from "@refinedev/antd";
import { Form, InputNumber, Select, DatePicker, Switch } from "antd";
import { useEffect, useState } from "react";
import type { Dayjs } from "dayjs";

import { axiosInstance } from "../../providers/axios";

interface TourOption {
  id: string;
  title: string;
}

interface FormValues {
  tour_id: string;
  dateRange: [Dayjs, Dayjs];
  price: number;
  total_quota: number;
  is_active?: boolean;
}

export const TourDepartureCreate = () => {
  const { formProps, saveButtonProps, form } = useForm<FormValues>();
  const [tours, setTours] = useState<TourOption[]>([]);

  useEffect(() => {
    axiosInstance
      .get("tours")
      .then((res) => setTours((res.data ?? []) as TourOption[]))
      .catch(() => setTours([]));
  }, []);

  const handleOnFinish = (values: Record<string, unknown>) => {
    const { tour_id, dateRange, price, total_quota, is_active } = values as unknown as FormValues;
    const startDate = dateRange[0].format("YYYY-MM-DD");
    const endDate = dateRange[1].format("YYYY-MM-DD");

    const submitData = {
      tour_id,
      start_date: startDate,
      end_date: endDate,
      price,
      total_quota,
      available_seats: total_quota,
      is_active: is_active ?? true,
    };

    formProps.onFinish?.(submitData);
  };

  return (
    <Create
      saveButtonProps={{
        ...saveButtonProps,
        onClick: () => form.submit(),
      }}
      title="Yeni Sefer (Stok) Aç"
    >
      <Form {...formProps} layout="vertical" onFinish={handleOnFinish}>
        <Form.Item
          label="Tur Seçin"
          name="tour_id"
          rules={[{ required: true, message: "Lütfen bir tur seçin." }]}
        >
          <Select allowClear placeholder="Sefer eklenecek turu seçin">
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

        <Form.Item label="Satışa Açık mı?" name="is_active" valuePropName="checked" initialValue={true}>
          <Switch />
        </Form.Item>
      </Form>
    </Create>
  );
};