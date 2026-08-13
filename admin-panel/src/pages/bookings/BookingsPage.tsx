import { useEffect, useState } from "react";
import { Button, List, Popconfirm, Select, Space, Table, Tag, Typography, message } from "antd";
import { axiosInstance } from "../../providers/axios";

type BookingStatus = "pending" | "confirmed" | "cancelled";
type PaymentStatus = "pending" | "paid" | "failed" | "refunded";

type BookingRecord = {
  id: string;
  user_email: string | null;
  user_full_name: string | null;
  tour_title: string | null;
  start_date: string | null;
  end_date: string | null;
  seat_count: number;
  total_price: number;
  status: BookingStatus;
  payment_id?: string | null;
  payment_status?: PaymentStatus | null;
  created_at: string;
};

const STATUS_META: Record<BookingStatus, { color: string; label: string }> = {
  pending: { color: "gold", label: "Bekliyor" },
  confirmed: { color: "green", label: "Onaylandı" },
  cancelled: { color: "red", label: "İptal" },
};

const PAYMENT_META: Record<PaymentStatus, { color: string; label: string }> = {
  pending: { color: "gold", label: "Ödeme Bekliyor" },
  paid: { color: "geekblue", label: "Ödendi" },
  failed: { color: "volcano", label: "Başarısız" },
  refunded: { color: "purple", label: "İade Edildi" },
};

export function BookingsPage() {
  const [data, setData] = useState<BookingRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [statusFilter, setStatusFilter] = useState<BookingStatus | "">("");
  const [loading, setLoading] = useState(false);

  const load = async (page = current, size = pageSize, status = statusFilter) => {
    setLoading(true);
    try {
      const { data: res } = await axiosInstance.get<{ data: BookingRecord[]; total: number }>(
        "/admin/bookings",
        {
          params: { page, page_size: size, ...(status ? { status } : {}) },
        },
      );
      setData(res.data);
      setTotal(res.total);
      setCurrent(page);
      setPageSize(size);
      setStatusFilter(status);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1, pageSize, statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refresh = () => load(current, pageSize, statusFilter);

  const confirmBooking = async (id: string) => {
    await axiosInstance.patch(`/admin/bookings/${id}`, { status: "confirmed" });
    message.success("Rezervasyon onaylandı ve fiyat sabitlendi.");
    refresh();
  };

  const cancelBooking = async (id: string) => {
    await axiosInstance.post(`/admin/bookings/${id}/cancel`);
    message.success("Rezervasyon iptal edildi, koltuklar stoğa geri verildi.");
    refresh();
  };

  const refundPayment = async (paymentId: string) => {
    await axiosInstance.post(`/admin/payments/${paymentId}/refund`);
    message.success("Ödeme iade edildi, rezervasyon iptal edildi.");
    refresh();
  };

  const markPaymentPaid = async (paymentId: string) => {
    await axiosInstance.post(`/admin/payments/${paymentId}/confirm`);
    message.success("Ödeme ödendi olarak işaretlendi, rezervasyon onaylandı.");
    refresh();
  };

  return (
    <List header="Rezervasyonlar">
      <Space style={{ marginBottom: 16 }}>
        <Typography.Text strong>Durum:</Typography.Text>
        <Select
          value={statusFilter}
          style={{ width: 180 }}
          onChange={(value) => load(current, pageSize, value)}
          options={[
            { value: "", label: "Tümü" },
            { value: "pending", label: "Bekliyor" },
            { value: "confirmed", label: "Onaylandı" },
            { value: "cancelled", label: "İptal" },
          ]}
        />
      </Space>

      <Table<BookingRecord>
        rowKey="id"
        dataSource={data}
        loading={loading}
        pagination={{
          current,
          pageSize,
          total,
          showSizeChanger: true,
          onChange: (page, size) => load(page, size, statusFilter),
        }}
      >
        <Table.Column<BookingRecord>
          title="ID"
          dataIndex="id"
          ellipsis
          render={(id: string) => <Typography.Text code>{id.slice(0, 8)}</Typography.Text>}
        />
        <Table.Column<BookingRecord>
          title="Kişi / Tur"
          key="tour"
          render={(_, r) => (
            <Space direction="vertical" size={0}>
              <Typography.Text strong>{r.tour_title ?? "-"}</Typography.Text>
              <Typography.Text type="secondary">
                {r.start_date ?? "-"} → {r.end_date ?? "-"}
              </Typography.Text>
              <Typography.Text type="secondary">
                {r.user_full_name ?? r.user_email ?? "-"}
              </Typography.Text>
            </Space>
          )}
        />
        <Table.Column<BookingRecord>
          title="Koltuk"
          dataIndex="seat_count"
          width={80}
          align="center"
        />
        <Table.Column<BookingRecord>
          title="Toplam"
          dataIndex="total_price"
          width={120}
          align="right"
          render={(price: number) => `${Number(price).toLocaleString("tr-TR")} ₺`}
        />
        <Table.Column<BookingRecord>
          title="Durum"
          dataIndex="status"
          width={110}
          render={(status: BookingStatus) => (
            <Tag color={STATUS_META[status].color}>{STATUS_META[status].label}</Tag>
          )}
        />
        <Table.Column<BookingRecord>
          title="Ödeme"
          key="payment"
          width={130}
          render={(_, r) =>
            r.payment_status ? (
              <Tag color={PAYMENT_META[r.payment_status].color}>
                {PAYMENT_META[r.payment_status].label}
              </Tag>
            ) : (
              <Tag>—</Tag>
            )
          }
        />
        <Table.Column<BookingRecord>
          title="İşlemler"
          key="actions"
          width={260}
          render={(_, r) => (
            <Space>
              {r.status === "pending" && (
                <Button type="primary" size="small" onClick={() => confirmBooking(r.id)}>
                  Onayla
                </Button>
              )}
              {r.payment_id && r.payment_status === "pending" && r.status === "pending" && (
                <Button type="default" size="small" onClick={() => markPaymentPaid(r.payment_id!)}>
                  Ödendi
                </Button>
              )}
              {r.payment_id && r.payment_status === "paid" && (
                <Popconfirm
                  cancelText="Vazgeç"
                  okText="İade Et"
                  title="Ödeme iade edilsin mi? Rezervasyon iptal edilir ve koltuklar stoğa döner."
                  onConfirm={() => refundPayment(r.payment_id!)}
                >
                  <Button size="small">İade Et</Button>
                </Popconfirm>
              )}
              {r.status !== "cancelled" && (
                <Popconfirm
                  cancelText="Vazgeç"
                  okText="İptal Et"
                  title="Rezervasyon iptal edilsin mi? Koltuklar stoğa geri döner."
                  onConfirm={() => cancelBooking(r.id)}
                >
                  <Button danger size="small">
                    İptal Et
                  </Button>
                </Popconfirm>
              )}
            </Space>
          )}
        />
      </Table>
    </List>
  );
}
