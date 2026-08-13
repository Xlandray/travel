import { useEffect, useState } from "react";
import { List, Select, Space, Table, Tag, Tooltip, Typography } from "antd";

import { axiosInstance } from "../../providers/axios";

type AuditAction =
  | "booking.created"
  | "booking.cancelled"
  | "booking.confirmed"
  | "booking.expired"
  | "payment.opened"
  | "payment.paid"
  | "payment.refunded";

type AuditRecord = {
  id: string;
  recorded_at: string;
  action: AuditAction;
  actor_id: string | null;
  actor_email: string | null;
  actor_is_superuser: boolean | null;
  booking_id: string | null;
  payment_id: string | null;
  amount: string | null;
  detail: Record<string, unknown> | null;
};

const ACTION_META: Record<AuditAction, { color: string; label: string }> = {
  "booking.created": { color: "blue", label: "Rezervasyon açıldı" },
  "booking.confirmed": { color: "green", label: "Rezervasyon onaylandı" },
  "booking.cancelled": { color: "red", label: "Rezervasyon iptal edildi" },
  "booking.expired": { color: "default", label: "Süre doldu (otomatik)" },
  "payment.opened": { color: "cyan", label: "Ödeme başlatıldı" },
  "payment.paid": { color: "geekblue", label: "Ödeme alındı" },
  "payment.refunded": { color: "purple", label: "Ödeme iade edildi" },
};

const ACTION_OPTIONS = [
  { value: "", label: "Tümü" },
  ...Object.entries(ACTION_META).map(([value, meta]) => ({ value, label: meta.label })),
];

function formatMoment(value: string): string {
  return new Date(value).toLocaleString("tr-TR");
}

/**
 * The trail, read-only.
 *
 * There is no edit or delete here and there is no endpoint behind one either:
 * a record an administrator can tidy up says nothing about administrators.
 */
export function AuditLogPage() {
  const [data, setData] = useState<AuditRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [actionFilter, setActionFilter] = useState<AuditAction | "">("");
  const [loading, setLoading] = useState(false);

  const load = async (page = current, size = pageSize, action = actionFilter) => {
    setLoading(true);
    try {
      const { data: res } = await axiosInstance.get<{ data: AuditRecord[]; total: number }>(
        "/admin/audit-logs",
        { params: { page, page_size: size, ...(action ? { action } : {}) } },
      );
      setData(res.data);
      setTotal(res.total);
      setCurrent(page);
      setPageSize(size);
      setActionFilter(action);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1, pageSize, actionFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <List header="Denetim Günlüğü">
      <Space style={{ marginBottom: 16 }} wrap>
        <Typography.Text strong>Olay:</Typography.Text>
        <Select
          value={actionFilter}
          style={{ width: 240 }}
          onChange={(value) => load(1, pageSize, value)}
          options={ACTION_OPTIONS}
        />
        <Typography.Text type="secondary">
          Kayıtlar yalnızca okunabilir; düzenlenemez veya silinemez.
        </Typography.Text>
      </Space>

      <Table<AuditRecord>
        rowKey="id"
        dataSource={data}
        loading={loading}
        pagination={{
          current,
          pageSize,
          total,
          showSizeChanger: true,
          onChange: (page, size) => load(page, size, actionFilter),
        }}
      >
        <Table.Column<AuditRecord>
          title="Zaman"
          dataIndex="recorded_at"
          width={170}
          render={(value: string) => (
            <Typography.Text type="secondary">{formatMoment(value)}</Typography.Text>
          )}
        />
        <Table.Column<AuditRecord>
          title="Olay"
          dataIndex="action"
          width={190}
          render={(action: AuditAction) => (
            <Tag color={ACTION_META[action].color}>{ACTION_META[action].label}</Tag>
          )}
        />
        <Table.Column<AuditRecord>
          title="Kim"
          key="actor"
          render={(_, r) =>
            r.actor_email ? (
              <Space direction="vertical" size={0}>
                <Typography.Text>{r.actor_email}</Typography.Text>
                {r.actor_is_superuser && <Tag color="gold">Yönetici</Tag>}
              </Space>
            ) : (
              <Tooltip title="Bir kişi değil, zaman aşımı süpürücüsü yaptı.">
                <Tag>Sistem</Tag>
              </Tooltip>
            )
          }
        />
        <Table.Column<AuditRecord>
          title="Tutar"
          dataIndex="amount"
          width={120}
          align="right"
          render={(amount: string | null) =>
            amount === null ? "—" : `${Number(amount).toLocaleString("tr-TR")} ₺`
          }
        />
        <Table.Column<AuditRecord>
          title="Rezervasyon / Ödeme"
          key="refs"
          width={200}
          render={(_, r) => (
            <Space direction="vertical" size={0}>
              {r.booking_id && (
                <Typography.Text code copyable={{ text: r.booking_id }}>
                  {r.booking_id.slice(0, 8)}
                </Typography.Text>
              )}
              {r.payment_id && (
                <Typography.Text code copyable={{ text: r.payment_id }} type="secondary">
                  {r.payment_id.slice(0, 8)}
                </Typography.Text>
              )}
            </Space>
          )}
        />
        <Table.Column<AuditRecord>
          title="Ayrıntı"
          dataIndex="detail"
          render={(detail: Record<string, unknown> | null) =>
            detail ? (
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {Object.entries(detail)
                  .map(([key, value]) => `${key}: ${String(value)}`)
                  .join(" · ")}
              </Typography.Text>
            ) : (
              "—"
            )
          }
        />
      </Table>
    </List>
  );
}
