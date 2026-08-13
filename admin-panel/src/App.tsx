import { Authenticated, Refine } from "@refinedev/core";
import routerProvider, { CatchAllNavigate } from "@refinedev/react-router";
import { ErrorComponent, RefineThemes, ThemedLayout } from "@refinedev/antd";
import { App as AntdApp, ConfigProvider } from "antd";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router";

import "@refinedev/antd/dist/reset.css";

import { LoginPage } from "./pages/LoginPage";
import { ResourceListPage } from "./pages/ResourceListPage";
import { Dashboard } from "./pages/Dashboard";
import { BookingsPage } from "./pages/bookings/BookingsPage";
import { TourCreate } from "./pages/tours/create";
import { TourEdit } from "./pages/tours/edit";
import { TourDepartureCreate } from "./pages/tour-departures/create";
import { TourDepartureEdit } from "./pages/tour-departures/edit";
import { TourCategoryForm } from "./pages/tour-categories/TourCategoryForm";
import { ContentForm } from "./pages/contents/ContentForm";
import { SettingsForm } from "./pages/settings/SettingsForm";
import { UserForm } from "./pages/users/UserForm";
import { HotelForm } from "./pages/hotels/HotelForm";
import { authProvider } from "./providers/authProvider";
import { dataProvider } from "./providers/dataProvider";

const resources = [
  {
    name: "admin/dashboard",
    list: "/dashboard",
    meta: { label: "Operasyon Paneli" },
  },
  {
    name: "admin/bookings",
    list: "/bookings",
    meta: { label: "Rezervasyonlar" },
  },
  {
    name: "tours",
    list: "/tours",
    create: "/tours/create",
    edit: "/tours/edit/:id",
    meta: { label: "Turlar" },
  },
  {
    name: "tour-departures",
    list: "/tour-departures",
    create: "/tour-departures/create",
    edit: "/tour-departures/edit/:id",
    meta: { label: "Seferler (Stok)" },
  },
  {
    name: "tour-categories",
    list: "/tour-categories",
    create: "/tour-categories/create",
    edit: "/tour-categories/edit/:id",
    meta: { label: "Tur Kategorileri" },
  },
  {
    name: "hotels",
    list: "/hotels",
    create: "/hotels/create",
    edit: "/hotels/edit/:id",
    meta: { label: "Oteller" },
  },
  {
    name: "admin/contents",
    list: "/contents",
    create: "/contents/create",
    edit: "/contents/edit/:id",
    meta: { label: "İçerikler" },
  },
  {
    name: "admin/settings",
    list: "/settings",
    create: "/settings/create",
    edit: "/settings/edit/:id",
    meta: { label: "Ayarlar" },
  },
  {
    name: "admin/users",
    list: "/users",
    edit: "/users/edit/:id",
    meta: { label: "Kullanıcılar" },
  },
];

export default function App() {
  return (
    <BrowserRouter>
      <ConfigProvider theme={RefineThemes.Blue}>
        <AntdApp>
          <Refine
            authProvider={authProvider}
            dataProvider={{ default: dataProvider }}
            routerProvider={routerProvider}
            resources={resources}
          >
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                element={
                  <Authenticated key="admin-auth" fallback={<CatchAllNavigate to="/login" />}>
                    <ThemedLayout>
                      <Outlet />
                    </ThemedLayout>
                  </Authenticated>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/bookings" element={<BookingsPage />} />
                <Route
                  path="/tours"
                  element={<ResourceListPage resource="tours" title="Turlar" />}
                />
                <Route path="/tours/create" element={<TourCreate />} />
                <Route path="/tours/edit/:id" element={<TourEdit />} />
                <Route
                  path="/tour-departures"
                  element={<ResourceListPage resource="tour-departures" title="Seferler (Stok)" />}
                />
                <Route path="/tour-departures/create" element={<TourDepartureCreate />} />
                <Route path="/tour-departures/edit/:id" element={<TourDepartureEdit />} />
                <Route
                  path="/tour-categories"
                  element={<ResourceListPage resource="tour-categories" title="Tur Kategorileri" />}
                />
                <Route
                  path="/tour-categories/create"
                  element={<TourCategoryForm mode="create" />}
                />
                <Route
                  path="/tour-categories/edit/:id"
                  element={<TourCategoryForm mode="edit" />}
                />
                <Route
                  path="/hotels"
                  element={<ResourceListPage resource="hotels" title="Oteller" />}
                />
                <Route path="/hotels/create" element={<HotelForm mode="create" />} />
                <Route path="/hotels/edit/:id" element={<HotelForm mode="edit" />} />
                <Route
                  path="/contents"
                  element={<ResourceListPage resource="admin/contents" title="İçerikler" />}
                />
                <Route path="/contents/create" element={<ContentForm mode="create" />} />
                <Route path="/contents/edit/:id" element={<ContentForm mode="edit" />} />
                <Route
                  path="/settings"
                  element={<ResourceListPage resource="admin/settings" title="Ayarlar" />}
                />
                <Route path="/settings/create" element={<SettingsForm mode="create" />} />
                <Route path="/settings/edit/:id" element={<SettingsForm mode="edit" />} />
                <Route
                  path="/users"
                  element={
                    <ResourceListPage
                      resource="admin/users"
                      title="Kullanıcılar"
                      canCreate={false}
                      canDelete={false}
                    />
                  }
                />
                <Route path="/users/edit/:id" element={<UserForm />} />
                <Route path="*" element={<ErrorComponent />} />
              </Route>
              <Route path="*" element={<Navigate replace to="/login" />} />
            </Routes>
          </Refine>
        </AntdApp>
      </ConfigProvider>
    </BrowserRouter>
  );
}
