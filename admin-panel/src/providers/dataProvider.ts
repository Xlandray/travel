import type {
  BaseRecord,
  CreateParams,
  CreateResponse,
  DataProvider,
  DeleteOneParams,
  DeleteOneResponse,
  GetListParams,
  GetListResponse,
  GetManyParams,
  GetManyResponse,
  GetOneParams,
  GetOneResponse,
  UpdateParams,
  UpdateResponse,
} from "@refinedev/core";

import { apiBaseUrl, axiosInstance } from "./axios";

type PageResponse<T> = { data: T[]; total: number };

export const dataProvider: DataProvider = {
  getList: async <TData extends BaseRecord = BaseRecord>({
    resource,
    pagination,
  }: GetListParams): Promise<GetListResponse<TData>> => {
    const current = pagination?.currentPage ?? 1;
    const pageSize = pagination?.pageSize ?? 25;
    const response = await axiosInstance.get<PageResponse<TData>>(`/${resource}`, {
      params: { page: current, page_size: pageSize },
    });
    return { data: response.data.data, total: response.data.total };
  },
  getOne: async <TData extends BaseRecord = BaseRecord>({
    resource,
    id,
  }: GetOneParams): Promise<GetOneResponse<TData>> => {
    const response = await axiosInstance.get<TData>(`/${resource}/${id}`);
    return { data: response.data };
  },
  getMany: async <TData extends BaseRecord = BaseRecord>({
    resource,
    ids,
  }: GetManyParams): Promise<GetManyResponse<TData>> => {
    const records = await Promise.all(
      ids.map(async (id) => {
        const response = await axiosInstance.get<TData>(`/${resource}/${id}`);
        return response.data;
      }),
    );
    return { data: records };
  },
  create: async <TData extends BaseRecord = BaseRecord, TVariables = object>({
    resource,
    variables,
  }: CreateParams<TVariables>): Promise<CreateResponse<TData>> => {
    const response = await axiosInstance.post<TData>(`/${resource}`, variables);
    return { data: response.data };
  },
  update: async <TData extends BaseRecord = BaseRecord, TVariables = object>({
    resource,
    id,
    variables,
  }: UpdateParams<TVariables>): Promise<UpdateResponse<TData>> => {
    const response = await axiosInstance.patch<TData>(`/${resource}/${id}`, variables);
    return { data: response.data };
  },
  deleteOne: async <TData extends BaseRecord = BaseRecord, TVariables = object>({
    resource,
    id,
  }: DeleteOneParams<TVariables>): Promise<DeleteOneResponse<TData>> => {
    await axiosInstance.delete(`/${resource}/${id}`);
    return { data: { id } as TData };
  },
  getApiUrl: () => apiBaseUrl,
};
