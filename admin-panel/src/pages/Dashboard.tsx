import { useEffect, useState } from "react";
import { Card, Col, Descriptions, Progress, Row, Statistic, Table, Typography } from "antd";
import { axiosInstance } from "../providers/axios";

type UpcomingDeparture = {
  departure_id: string;
  tour_title: string;
  start_date: string;
  end_date: string;
  price: number;
  total_quota: number;
  available_seats: number;
  sold_seats: number;
  occupancy_percent: number;
};

type BookingSummary = {
  id: string;
  tour_title: string;
  user_email: string;
  seat_count: number;
  total_price: number;
  status: "pending" | "confirmed" | "cancelled";
  created_at: string;
};

type DashboardData = {
  total_tours: number;
  total_departures: number;
  total_bookings: number;
  pending_bookings: number;
  confirmed_bookings: number;
  cancelled_bookings: number;
  sold_seats_total: number;
  confirmed_revenue: number;
  upcoming_departures: UpcomingDeparture[];
  recent_bookings: BookingSummary[];
};

const STATUS_LABEL: Record<BookingSummary["status"], string> = {
  pending: "Bekliyor",
  confirmed: "Onaylandı",
  cancelled: "İptal",
};

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    axiosInstance.get<DashboardData>("/admin/dashboard").then(({ data }) => setData(data));
  }, []);

  return (
    <div>
      <Typography.Title level={3}>Operasyon Paneli</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Tur Sayısı" value={data?.total_tours ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Sefer Sayısı" value={data?.total_departures ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Toplam Rezervasyon" value={data?.total_bookings ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic
              title="Onaylı Gelir"
              value={data?.confirmed_revenue ?? 0}
              precision={2}
              suffix="₺"
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Satılan Koltuk (Aktif)" value={data?.sold_seats_total ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Bekleyen (Kilitleme)" value={data?.pending_bookings ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Onaylı" value={data?.confirmed_bookings ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="İptal" value={data?.cancelled_bookings ?? 0} />
          </Card>
        </Col>
      </Row>

      <Card title="Yaklaşan Seferler ve Doluluk" style={{ marginTop: 24 }}>
        <Table<UpcomingDeparture>
          rowKey="departure_id"
          dataSource={data?.upcoming_departures ?? []}
          pagination={false}
          size="small"
        >
          <Table.Column<UpcomingDeparture> title="Tur" dataIndex="tour_title" />
          <Table.Column<UpcomingDeparture>
            title="Tarih"
            render={(_, r) => `${r.start_date} → ${r.end_date}`}
          />
          <Table.Column<UpcomingDeparture>
            title="Fiyat"
            align="right"
            render={(_, r) => `${Number(r.price).toLocaleString("tr-TR")} ₺`}
          />
          <Table.Column<UpcomingDeparture>
            title="Satılan"
            align="center"
            render={(_, r) => `${r.sold_seats}/${r.total_quota}`}
          />
          <Table.Column<UpcomingDeparture>
            title="Doluluk"
            dataIndex="occupancy_percent"
            render={(value: number) => (
              <Progress percent={value} size="small" status={value >= 90 ? "exception" : "active"} />
            )}
          />
        </Table>
      </Card>

      <Card title="Son Rezervasyonlar" style={{ marginTop: 24 }}>
        <Table<BookingSummary>
          rowKey="id"
          dataSource={data?.recent_bookings ?? []}
          pagination={false}
          size="small"
        >
          <Table.Column<BookingSummary> title="Tur" dataIndex="tour_title" />
          <Table.Column<BookingSummary> title="Kişi" dataIndex="user_email" />
          <Table.Column<BookingSummary> title="Koltuk" dataIndex="seat_count" align="center" />
          <Table.Column<BookingSummary>
            title="Tutar"
            align="right"
            render={(_, r) => `${Number(r.total_price).toLocaleString("tr-TR")} ₺`}
          />
          <Table.Column<BookingSummary>
            title="Durum"
            dataIndex="status"
            render={(status: BookingSummary["status"]) => STATUS_LABEL[status]}
          />
        </Table>
      </Card>

      <Card title="Stok Kilitleme Bilgisi" style={{ marginTop: 24 }}>
        <Descriptions
          column={1}
          size="small"
          items={[
            {
              key: "lock",
              label: "Mekanizma",
              children:
                "Koltuklar rezervasyon anında with_for_update ile kilitlenirler; PENDING rezervasyonlar 15 dakika sonunda iptal edilip stok geri alınır.",
            },
          ]}
        />
      </Card>
    </div>
  );
}