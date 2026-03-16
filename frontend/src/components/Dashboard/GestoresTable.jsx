// frontend/src/components/Dashboard/GestoresTable.jsx
// Tabla de gestores con drill-down expandible, filtros y variación sep→oct

import React, { useState, useEffect, useMemo } from 'react';
import { Table, Tag, Badge, Progress, Skeleton, Select, Space, Typography, Card } from 'antd';
import api from '../../services/api';

const { Text } = Typography;

const SEGMENTO_COLORS = {
  'N10102': '#A100FF', // Privada
  'N10103': '#7B00CC', // Empresas
  'N10101': '#CC66FF', // Minorista
  'N10104': '#00B8F5', // Personal
  'N20301': '#5500AA', // Fondos
};

const normPeriodo = (p) =>
  typeof p === 'object' ? p?.latest || p?.periodo || '2025-10' : p || '2025-10';

const GestoresTable = ({ periodo }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState([]);
  const [expandedData, setExpandedData] = useState({});
  const [loadingExpand, setLoadingExpand] = useState({});
  const [segmentoFilter, setSegmentoFilter] = useState(null);
  const [centroFilter, setCentroFilter] = useState(null);

  useEffect(() => {
    if (!periodo) return;
    let active = true;
    setLoading(true);

    const curr = normPeriodo(periodo);
    const prev = curr === '2025-10' ? '2025-09' : null;

    const calls = [
      api.charts.gestoresRanking({ metric: 'INGRESOS', periodo: curr }),
      prev
        ? api.charts.gestoresRanking({ metric: 'INGRESOS', periodo: prev })
        : Promise.resolve(null),
    ];

    Promise.all(calls)
      .then(([currRes, prevRes]) => {
        if (!active) return;

        const currRows = currRes?.chart?.data || [];
        const prevMap = {};
        if (prevRes) {
          (prevRes?.chart?.data || []).forEach((r) => {
            const d = r.original_data || r;
            prevMap[d.GESTOR_ID] = d.ingresos_total || 0;
          });
        }

        const rows = currRows.map((r) => {
          const d = r.original_data || r;
          const prevIngresos = prevMap[d.GESTOR_ID];
          const variation =
            prevIngresos && prevIngresos !== 0
              ? Math.round(((d.ingresos_total - prevIngresos) / Math.abs(prevIngresos)) * 1000) / 10
              : null;

          return {
            key: d.GESTOR_ID,
            gestor_id: d.GESTOR_ID,
            nombre: d.DESC_GESTOR,
            segmento_id: d.SEGMENTO_ID,
            segmento: d.DESC_SEGMENTO,
            centro: d.DESC_CENTRO,
            ingresos: d.ingresos_total || 0,
            margen: d.margen_neto || 0,
            cartera: d.n_contratos || 0,
            variation,
          };
        });

        setData(rows);
      })
      .catch((e) => console.error('[GestoresTable] Error:', e))
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [periodo]);

  const handleExpand = async (expanded, record) => {
    if (!expanded || expandedData[record.gestor_id] !== undefined) return;
    setLoadingExpand((prev) => ({ ...prev, [record.gestor_id]: true }));
    try {
      const productos = await api.basic.productosByGestor(record.gestor_id);
      setExpandedData((prev) => ({ ...prev, [record.gestor_id]: productos || [] }));
    } catch {
      setExpandedData((prev) => ({ ...prev, [record.gestor_id]: [] }));
    } finally {
      setLoadingExpand((prev) => ({ ...prev, [record.gestor_id]: false }));
    }
  };

  const segmentoOptions = useMemo(() => {
    const segs = [...new Map(data.map((r) => [r.segmento_id, r.segmento])).entries()];
    return segs.map(([value, label]) => ({ value, label }));
  }, [data]);

  const centroOptions = useMemo(() => {
    const centros = [...new Set(data.map((r) => r.centro))];
    return centros.map((c) => ({ value: c, label: c }));
  }, [data]);

  const filteredData = useMemo(
    () =>
      data
        .filter((r) => !segmentoFilter || r.segmento_id === segmentoFilter)
        .filter((r) => !centroFilter || r.centro === centroFilter),
    [data, segmentoFilter, centroFilter]
  );

  const columns = [
    {
      title: 'Gestor',
      dataIndex: 'nombre',
      key: 'nombre',
      render: (text) => <Text strong style={{ fontSize: 13 }}>{text}</Text>,
    },
    {
      title: 'Segmento',
      dataIndex: 'segmento',
      key: 'segmento',
      render: (text, record) => (
        <Badge
          color={SEGMENTO_COLORS[record.segmento_id] || '#999'}
          text={<Text style={{ fontSize: 12 }}>{text}</Text>}
        />
      ),
    },
    {
      title: 'Centro',
      dataIndex: 'centro',
      key: 'centro',
      render: (text) => <Text style={{ fontSize: 12 }}>{text}</Text>,
    },
    {
      title: 'Ingresos del Mes',
      dataIndex: 'ingresos',
      key: 'ingresos',
      sorter: (a, b) => a.ingresos - b.ingresos,
      defaultSortOrder: 'descend',
      render: (val) => (
        <Text strong>
          {new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR',
            maximumFractionDigits: 0,
          }).format(val)}
        </Text>
      ),
    },
    {
      title: 'Margen %',
      dataIndex: 'margen',
      key: 'margen',
      sorter: (a, b) => a.margen - b.margen,
      render: (val) => (
        <Space direction="vertical" size={2} style={{ width: '100%', minWidth: 90 }}>
          <Text style={{ fontSize: 12 }}>{(val || 0).toFixed(1)}%</Text>
          <Progress
            percent={Math.min(Math.max(val || 0, 0), 100)}
            size="small"
            strokeColor="#A100FF"
            showInfo={false}
          />
        </Space>
      ),
    },
    {
      title: 'Cartera',
      dataIndex: 'cartera',
      key: 'cartera',
      sorter: (a, b) => a.cartera - b.cartera,
      render: (val) => <Text>{val}</Text>,
    },
    {
      title: 'Var. sep→oct',
      dataIndex: 'variation',
      key: 'variation',
      sorter: (a, b) => (a.variation || 0) - (b.variation || 0),
      render: (val) => {
        if (val === null || val === undefined)
          return <Text type="secondary" style={{ fontSize: 12 }}>—</Text>;
        const isPos = val >= 0;
        return (
          <Tag
            style={{
              margin: 0,
              fontSize: 12,
              fontWeight: 600,
              color: isPos ? '#52c41a' : '#E5002B',
              borderColor: isPos ? '#52c41a' : '#E5002B',
              backgroundColor: isPos ? '#f6ffed' : '#fff2f0',
            }}
          >
            {val > 0 ? '+' : ''}{val.toFixed(1)}%
          </Tag>
        );
      },
    },
  ];

  const expandedRowRender = (record) => {
    if (loadingExpand[record.gestor_id]) {
      return <Skeleton active paragraph={{ rows: 2 }} style={{ padding: 16 }} />;
    }
    const productos = expandedData[record.gestor_id] || [];
    if (!productos.length) {
      return (
        <Text type="secondary" style={{ padding: 16, display: 'block', fontSize: 12 }}>
          Sin datos de productos disponibles
        </Text>
      );
    }
    const prodColumns = [
      {
        title: 'Producto',
        dataIndex: 'DESC_PRODUCTO',
        key: 'prod',
        render: (t) => <Text style={{ fontSize: 12 }}>{t}</Text>,
      },
      {
        title: 'Contratos',
        dataIndex: 'num_contratos',
        key: 'contratos',
        render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text>,
      },
    ];
    return (
      <Table
        columns={prodColumns}
        dataSource={productos.map((p, i) => ({ ...p, key: i }))}
        size="small"
        pagination={false}
        style={{ margin: '0 48px 8px' }}
      />
    );
  };

  if (loading) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="Filtrar por Segmento"
          allowClear
          style={{ minWidth: 190 }}
          options={segmentoOptions}
          onChange={setSegmentoFilter}
        />
        <Select
          placeholder="Filtrar por Centro"
          allowClear
          style={{ minWidth: 190 }}
          options={centroOptions}
          onChange={setCentroFilter}
        />
        <Text type="secondary" style={{ fontSize: 12 }}>
          {filteredData.length} gestores
        </Text>
      </Space>
      <Table
        columns={columns}
        dataSource={filteredData}
        size="small"
        expandable={{
          expandedRowRender,
          onExpand: handleExpand,
        }}
        pagination={{ pageSize: 15, showSizeChanger: false }}
        scroll={{ x: 820 }}
        rowHoverable
      />
    </div>
  );
};

export default GestoresTable;
