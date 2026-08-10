import { useDelete } from "@refinedev/core";
import { List, useTable } from "@refinedev/antd";
import { Button, Popconfirm, Space, Table, Tag, Typography } from "antd";
import { useNavigate } from "react-router";

type ResourceRecord = { id: string; [key: string]: unknown };

type ColumnDef<T = Record<string, unknown>> = {
  title: string;
  dataIndex?: string;
  width?: number;
  render?: (value: unknown, record: T) => React.ReactNode;
};

type ResourceListPageProps = {
  resource: string;
  title: string;
  canCreate?: boolean;
  canDelete?: boolean;
};

function formatDate(value: unknown): string {
  if (!value) return "-";
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString("tr-TR");
}

function formatPrice(value: unknown): string {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toLocaleString("tr-TR")} ₺` : "-";
}

function StatusTag({ active }: { active: unknown }) {
  return active ? (
    <Tag color="success">Aktif</Tag>
  ) : (
    <Tag color="error">Pasif</Tag>
  );
}

function thumbnail(url: unknown, alt = "Görsel") {
  if (!url) return <span style={{ color: "#999" }}>—</span>;
  const src = typeof url === "string" && url.startsWith("http") ? url : undefined;
  return (
    <img
      src={src || (typeof url === "string" ? url : undefined)}
      alt={alt}
      style={{ width: 48, height: 36, objectFit: "cover", borderRadius: 6, background: "#eee" }}
      onError={(e) => {
        (e.currentTarget as HTMLImageElement).style.visibility = "hidden";
      }}
    />
  );
}

const COLUMNS: Record<string, ColumnDef<ResourceRecord>[]> = {
  tours: [
    {
      title: "Kapak",
      width: 70,
      render: (_, record) => thumbnail(record.image_url, String(record.title ?? "")),
    },
    { title: "Başlık", dataIndex: "title", render: (v) => <strong>{String(v)}</strong> },
    {
      title: "Kategori",
      render: (_, record) => {
        const cat = record.category as { name?: string } | null;
        return cat?.name ? <Tag>{cat.name}</Tag> : "—";
      },
    },
    { title: "Fiyat", dataIndex: "price", width: 100, render: formatPrice },
    {
      title: "Süre",
      width: 110,
      render: (_, record) => {
        const days = Number(record.days ?? 0);
        const nights = Number(record.nights ?? 0);
        return `${days} gün${nights > 0 ? ` / ${nights} gece` : ""}`;
      },
    },
    {
      title: "Sefer",
      width: 80,
      render: (_, record) => {
        const count = Array.isArray(record.departures) ? record.departures.length : 0;
        return count > 0 ? <Tag color="blue">{count}</Tag> : "—";
      },
    },
    {
      title: "Durum",
      width: 90,
      render: (_, record) => <StatusTag active={record.is_active} />,
    },
  ],
  "tour-departures": [
    {
      title: "Tur",
      render: (_, record) => String(record.tour_id ?? "-").slice(0, 8),
    },
    { title: "Gidiş", dataIndex: "start_date", width: 110, render: formatDate },
    { title: "Dönüş", dataIndex: "end_date", width: 110, render: formatDate },
    { title: "Fiyat", dataIndex: "price", width: 100, render: formatPrice },
    {
      title: "Koltuk",
      width: 110,
      render: (_, record) => (
        <span>
          <strong>{String(record.available_seats ?? "-")}</strong> / {String(record.total_quota ?? "-")}
        </span>
      ),
    },
    {
      title: "Durum",
      width: 90,
      render: (_, record) => <StatusTag active={record.is_active} />,
    },
  ],
  "tour-categories": [
    { title: "Ad", dataIndex: "name", render: (v) => <strong>{String(v)}</strong> },
    { title: "Slug", dataIndex: "slug", render: (v) => <Typography.Text code>{String(v)}</Typography.Text> },
    {
      title: "Durum",
      width: 90,
      render: (_, record) => <StatusTag active={record.is_active} />,
    },
  ],
  "admin/users": [
    { title: "E-posta", dataIndex: "email", render: (v) => <strong>{String(v)}</strong> },
    { title: "Ad Soyad", dataIndex: "full_name", render: (v) => String(v ?? "—") },
    {
      title: "Rol",
      width: 120,
      render: (_, record) =>
        record.is_superuser ? <Tag color="gold">Süper Admin</Tag> : <Tag>Kullanıcı</Tag>,
    },
    {
      title: "Durum",
      width: 90,
      render: (_, record) => <StatusTag active={record.is_active} />,
    },
    { title: "Kayıt", dataIndex: "created_at", width: 120, render: formatDate },
  ],
  "admin/contents": [
    { title: "Başlık", dataIndex: "title", render: (v) => <strong>{String(v ?? "—")}</strong> },
    { title: "Slug", dataIndex: "slug", render: (v) => <Typography.Text code>{String(v ?? "—")}</Typography.Text> },
    {
      title: "Durum",
      width: 90,
      render: (_, record) => <StatusTag active={record.is_active} />,
    },
    { title: "Kayıt", dataIndex: "created_at", width: 120, render: formatDate },
  ],
  "admin/settings": [
    { title: "Anahtar", dataIndex: "key", render: (v) => <Typography.Text code>{String(v ?? "—")}</Typography.Text> },
    {
      title: "Değer",
      dataIndex: "value",
      render: (v) => String(v ?? "—"),
    },
    {
      title: "Açıklama",
      dataIndex: "description",
      render: (v) => String(v ?? "—"),
    },
  ],
};

export function ResourceListPage({
  resource,
  title,
  canCreate = true,
  canDelete = true,
}: ResourceListPageProps) {
  const navigate = useNavigate();
  const { tableProps } = useTable<ResourceRecord>({ resource });
  const { mutate: deleteRecord } = useDelete();
  const createButton = canCreate ? (
    <Button type="primary" onClick={() => navigate(`/${resource.split("/").at(-1)}/create`)}>
      Oluştur
    </Button>
  ) : null;

  const columns = COLUMNS[resource] ?? [
    { title: "ID", dataIndex: "id", render: (v: unknown) => <Typography.Text code>{String(v)}</Typography.Text> },
  ];

  return (
    <List title={title} headerButtons={createButton}>
      <Table<ResourceRecord> {...tableProps} rowKey="id" scroll={{ x: "max-content" }}>
        {columns.map((col) => (
          <Table.Column<ResourceRecord>
            key={col.title}
            title={col.title}
            dataIndex={col.dataIndex}
            width={col.width}
            render={col.render}
          />
        ))}
        <Table.Column<ResourceRecord>
          title="İşlemler"
          width={150}
          render={(_, record) => (
            <Space>
              <Button onClick={() => navigate(`/${resource.split("/").at(-1)}/edit/${record.id}`)}>
                Düzenle
              </Button>
              {canDelete ? (
                <Popconfirm
                  cancelText="Vazgeç"
                  okText="Sil"
                  title="Bu kayıt silinsin mi?"
                  onConfirm={() => deleteRecord({ resource, id: record.id })}
                >
                  <Button danger>Sil</Button>
                </Popconfirm>
              ) : null}
            </Space>
          )}
        />
      </Table>
    </List>
  );
}
