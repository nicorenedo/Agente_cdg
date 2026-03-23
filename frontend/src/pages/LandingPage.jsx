// src/pages/LandingPage.jsx
// Landing Page v6.0 — Three.js Neural Network + Glassmorphism + Framer-Motion

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button, Select, Typography, Space, Spin, App,
  Badge, Tooltip, Divider, Alert
} from 'antd';
import {
  ArrowRightOutlined, UserOutlined, TeamOutlined, DashboardOutlined,
  ReloadOutlined, SearchOutlined, CrownOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';

import api from '../services/api';

const { Option } = Select;
const { Text } = Typography;

/* ────────────────────────────────────────────────
 * Neural Network CSS animation (CSS fallback)
 * ──────────────────────────────────────────────── */
const NEURAL_CSS = `
@keyframes float-node {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.6; }
  33% { transform: translate(8px, -12px) scale(1.1); opacity: 0.9; }
  66% { transform: translate(-6px, 8px) scale(0.9); opacity: 0.7; }
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 6px rgba(161,0,255,0.4), 0 0 12px rgba(161,0,255,0.2); }
  50% { box-shadow: 0 0 14px rgba(161,0,255,0.8), 0 0 28px rgba(161,0,255,0.4); }
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}
`;

/* ────────────────────────────────────────────────
 * ThreeJsCanvas — Neural network background
 * ──────────────────────────────────────────────── */
const ThreeJsCanvas = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    let renderer, scene, camera, animFrameId;
    let resizeHandler;

    const initThree = () => {
      const THREE = window.THREE;
      const canvas = canvasRef.current;
      if (!THREE || !canvas) return;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
      camera.position.z = 6;

      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);

      // Build node positions
      const nodeCount = 80;
      const nodePositions = [];
      for (let i = 0; i < nodeCount; i++) {
        nodePositions.push({
          x: (Math.random() - 0.5) * 14,
          y: (Math.random() - 0.5) * 9,
          z: (Math.random() - 0.5) * 6,
        });
      }

      // Points (nodes)
      const pointsGeo = new THREE.BufferGeometry();
      const posArr = new Float32Array(nodeCount * 3);
      nodePositions.forEach((p, i) => {
        posArr[i * 3] = p.x;
        posArr[i * 3 + 1] = p.y;
        posArr[i * 3 + 2] = p.z;
      });
      pointsGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
      const pointsMat = new THREE.PointsMaterial({ color: 0xa100ff, size: 0.25, transparent: true, opacity: 0.9 });
      const points = new THREE.Points(pointsGeo, pointsMat);

      // Lines (connections)
      const lineVerts = [];
      const maxDist = 4.2;
      for (let i = 0; i < nodeCount; i++) {
        for (let j = i + 1; j < nodeCount; j++) {
          const dx = nodePositions[i].x - nodePositions[j].x;
          const dy = nodePositions[i].y - nodePositions[j].y;
          const dz = nodePositions[i].z - nodePositions[j].z;
          if (Math.sqrt(dx * dx + dy * dy + dz * dz) < maxDist) {
            lineVerts.push(nodePositions[i].x, nodePositions[i].y, nodePositions[i].z);
            lineVerts.push(nodePositions[j].x, nodePositions[j].y, nodePositions[j].z);
          }
        }
      }
      const lineGeo = new THREE.BufferGeometry();
      lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(lineVerts), 3));
      const lineMat = new THREE.LineBasicMaterial({ color: 0xa100ff, transparent: true, opacity: 0.25 });
      const lines = new THREE.LineSegments(lineGeo, lineMat);

      const group = new THREE.Group();
      group.add(points);
      group.add(lines);
      scene.add(group);

      const animate = () => {
        animFrameId = requestAnimationFrame(animate);
        group.rotation.y += 0.0008;
        group.rotation.x += 0.0003;
        renderer.render(scene, camera);
      };
      animate();

      resizeHandler = () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      };
      window.addEventListener('resize', resizeHandler);
    };

    if (window.THREE) {
      initThree();
    } else {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js';
      script.crossOrigin = 'anonymous';
      script.onload = initThree;
      script.onerror = () => console.warn('[Landing] Three.js CDN failed — CSS fallback active');
      document.head.appendChild(script);
    }

    return () => {
      cancelAnimationFrame(animFrameId);
      if (renderer) renderer.dispose();
      if (resizeHandler) window.removeEventListener('resize', resizeHandler);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
};

/* ────────────────────────────────────────────────
 * LandingPage Content
 * ──────────────────────────────────────────────── */
const LandingPageContent = () => {
  const navigate = useNavigate();
  const { message, notification } = App.useApp();

  const [gestores, setGestores] = useState([]);
  const [selectedGestor, setSelectedGestor] = useState(null);
  const [selectedGestorInfo, setSelectedGestorInfo] = useState(null);
  const [loadingGestores, setLoadingGestores] = useState(false);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState('checking');

  const fetchGestores = useCallback(async () => {
    setLoadingGestores(true);
    setSystemStatus('loading');
    setError(null);

    try {
      const rows = await api.basic.allGestores();
      const list = Array.isArray(rows) ? rows : [];

      const mapped = list
        .map((g) => {
          const id = g.GESTOR_ID || g.gestor_id || g.id || null;
          const nombre = g.DESC_GESTOR || g.nombre || g.desc_gestor || null;
          if (!id || !nombre) return null;
          const centro = g.DESC_CENTRO || g.centro || g.CENTRO || 'Centro no especificado';
          const segmento = g.DESC_SEGMENTO || g.segmento || g.SEGMENTO_ID || 'Segmento no especificado';
          return {
            id: String(id),
            nombre: String(nombre),
            centro: String(centro),
            segmento: String(segmento),
            displayName: `${String(nombre)} — ${String(centro)}`,
          };
        })
        .filter(Boolean)
        .sort((a, b) => a.nombre.localeCompare(b.nombre));

      if (!mapped.length) throw new Error('Sin gestores disponibles');

      setGestores(mapped);
      setSelectedGestor(mapped[0].id);
      setSelectedGestorInfo(mapped[0]);
      setSystemStatus('healthy');
      message.success(`${mapped.length} gestores cargados`);
    } catch (err) {
      const fallback = [
        { id: '18', nombre: 'Laia Vila Costa', centro: 'BARCELONA-BALMES', segmento: 'Banca Personal', displayName: 'Laia Vila Costa — BARCELONA-BALMES' },
        { id: '1', nombre: 'Antonio Rodríguez García', centro: 'MADRID-OFICINA PRINCIPAL', segmento: 'Banca Minorista', displayName: 'Antonio Rodríguez García — MADRID-OFICINA PRINCIPAL' },
      ];
      setGestores(fallback);
      setSelectedGestor(fallback[0].id);
      setSelectedGestorInfo(fallback[0]);
      setError('Conexión limitada – datos de demostración');
      setSystemStatus('error');
      notification.error({ message: 'API no disponible', description: err?.message, duration: 4 });
    } finally {
      setLoadingGestores(false);
    }
  }, [message, notification]);

  useEffect(() => { fetchGestores(); }, [fetchGestores]);

  const handleGestorChange = (id) => {
    setSelectedGestor(id);
    setSelectedGestorInfo(gestores.find((g) => g.id === id) || null);
  };

  const handleNavigateGestor = () => {
    if (!selectedGestor) { message.warning('Selecciona un gestor'); return; }
    navigate(`/gestor-dashboard?gestor=${encodeURIComponent(selectedGestor)}`);
  };

  const handleNavigateDireccion = () => navigate('/direccion-dashboard');

  /* ─── Glassmorphism card styles ─── */
  const glassCard = {
    background: 'rgba(161, 0, 255, 0.08)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid rgba(161, 0, 255, 0.3)',
    borderRadius: 20,
    padding: '32px 28px',
  };

  const glassBtn = {
    background: 'rgba(161, 0, 255, 0.15)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(161, 0, 255, 0.4)',
    color: '#F0E6FF',
    fontWeight: 600,
    borderRadius: 10,
    height: 48,
  };

  const glassBtnPrimary = {
    ...glassBtn,
    background: 'linear-gradient(135deg, rgba(161,0,255,0.7), rgba(230,0,200,0.5))',
    border: '1px solid rgba(161,0,255,0.6)',
    boxShadow: '0 0 20px rgba(161,0,255,0.3)',
  };

  return (
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden', background: '#0A0014' }}>
      {/* Inject CSS keyframes */}
      <style>{NEURAL_CSS}</style>

      {/* Three.js Canvas */}
      <ThreeJsCanvas />

      {/* Botón Actualizar — top-right */}
      <Tooltip title="Actualizar gestores">
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchGestores}
          loading={loadingGestores}
          style={{
            ...glassBtn,
            position: 'absolute',
            top: 20,
            right: 24,
            zIndex: 10,
            minWidth: 44,
          }}
        />
      </Tooltip>

      {/* Radial gradient overlay */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        background: 'radial-gradient(ellipse at 50% 0%, rgba(161,0,255,0.15) 0%, transparent 70%)',
      }} />

      {/* Content layer */}
      <div style={{
        position: 'relative',
        zIndex: 1,
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '2rem',
      }}>
        {/* Status badge */}
        {systemStatus !== 'healthy' && (
          <Badge
            status={systemStatus === 'loading' ? 'processing' : systemStatus === 'error' ? 'error' : 'warning'}
            text={<Text style={{ color: '#A87BC8', fontSize: 12 }}>
              {systemStatus === 'loading' ? 'Cargando…' : systemStatus === 'error' ? 'Conexión limitada' : 'Verificando'}
            </Text>}
            style={{ position: 'absolute', top: 24, right: 24 }}
          />
        )}

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          style={{ textAlign: 'center', marginBottom: 48 }}
        >
          <div style={{
            color: '#ffffff',
            fontWeight: 800,
            fontSize: 52,
            letterSpacing: '-2px',
            lineHeight: 1.1,
            textShadow: '0 0 40px rgba(161,0,255,0.8), 0 0 80px rgba(161,0,255,0.4)',
            marginBottom: 8,
          }}>
            <span style={{ color: '#CC66FF', marginRight: 10, fontSize: 56 }}>{'>'}</span>
            CDG Intelligence
          </div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            style={{ color: '#A87BC8', fontSize: 14, letterSpacing: 3, marginTop: 6 }}
          >
            COPILOTO DE CONTROL DE GESTIÓN · POWERED BY ACCENTURE
          </motion.div>
        </motion.div>

        {/* Cards */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          style={{ width: '100%', maxWidth: 1100, display: 'flex', gap: 28, flexWrap: 'wrap', justifyContent: 'center' }}
        >
          {/* Panel Gestor */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            style={{ flex: '1 1 440px', maxWidth: 500 }}
          >
            <div style={glassCard}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <UserOutlined style={{ fontSize: 40, color: '#CC66FF' }} />
                  <div style={{ color: '#F0E6FF', fontWeight: 700, fontSize: 22, marginTop: 10 }}>Panel Personal</div>
                  <div style={{ color: '#A87BC8', fontSize: 13, marginTop: 4 }}>Vista individual del gestor comercial</div>
                </div>

                <div>
                  <Text style={{ color: '#A87BC8', fontSize: 12, marginBottom: 8, display: 'block' }}>
                    Seleccionar Gestor Comercial
                  </Text>
                  <Select
                    showSearch
                    placeholder="🔍 Buscar gestor…"
                    value={selectedGestor}
                    onChange={handleGestorChange}
                    loading={loadingGestores}
                    size="large"
                    style={{ width: '100%' }}
                    disabled={loadingGestores || gestores.length === 0}
                    suffixIcon={<SearchOutlined />}
                    optionFilterProp="children"
                    filterOption={(input, option) =>
                      option?.children?.toLowerCase().includes(input.toLowerCase())
                    }
                    notFoundContent={loadingGestores ? <Spin size="small" /> : 'Sin resultados'}
                  >
                    {gestores.map((g) => (
                      <Option key={g.id} value={g.id}>{g.displayName}</Option>
                    ))}
                  </Select>
                </div>

                {selectedGestorInfo && (
                  <div style={{
                    background: 'rgba(161,0,255,0.1)',
                    border: '1px solid rgba(161,0,255,0.25)',
                    borderRadius: 10,
                    padding: '12px 16px',
                  }}>
                    <Text strong style={{ color: '#F0E6FF', display: 'block' }}>{selectedGestorInfo.nombre}</Text>
                    <Text style={{ color: '#A87BC8', fontSize: 12 }}>{selectedGestorInfo.centro} · {selectedGestorInfo.segmento}</Text>
                  </div>
                )}

                <Button
                  size="large"
                  icon={<ArrowRightOutlined />}
                  onClick={handleNavigateGestor}
                  disabled={!selectedGestor}
                  loading={loadingGestores}
                  style={{ ...glassBtnPrimary, width: '100%' }}
                >
                  Acceder a Mi Panel
                </Button>
              </Space>
            </div>
          </motion.div>

          {/* Panel Dirección */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.45 }}
            style={{ flex: '1 1 380px', maxWidth: 460 }}
          >
            <div style={{ ...glassCard, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '100%' }}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <DashboardOutlined style={{ fontSize: 40, color: '#CC66FF' }} />
                  <div style={{ color: '#F0E6FF', fontWeight: 700, fontSize: 22, marginTop: 10 }}>Panel Ejecutivo</div>
                  <div style={{ color: '#A87BC8', fontSize: 13, marginTop: 4 }}>Control de Gestión corporativo</div>
                </div>

                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                  {[
                    { icon: <TeamOutlined />, text: 'Consolidado de 30 gestores' },
                    { icon: <ThunderboltOutlined />, text: 'KPIs en tiempo real' },
                    { icon: <DashboardOutlined />, text: 'Modelo de Fábrica y ROE' },
                  ].map(({ icon, text }, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + i * 0.1 }}
                      style={{ display: 'flex', alignItems: 'center', gap: 10 }}
                    >
                      <span style={{ color: '#A100FF' }}>{icon}</span>
                      <Text style={{ color: '#A87BC8', fontSize: 13 }}>{text}</Text>
                    </motion.div>
                  ))}
                </Space>

                <Button
                  size="large"
                  icon={<CrownOutlined />}
                  onClick={handleNavigateDireccion}
                  style={{ ...glassBtnPrimary, width: '100%', marginTop: 8 }}
                >
                  Acceder al Panel Ejecutivo
                </Button>
              </Space>
            </div>
          </motion.div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          style={{ position: 'absolute', bottom: 28, color: '#6B4F7A', fontSize: 12, textAlign: 'center' }}
        >
          <Space split={<Divider type="vertical" style={{ borderColor: 'rgba(161,0,255,0.2)' }} />}>
            <span>CDG Intelligence ©2025 Accenture</span>
            <span>{gestores.length} gestores disponibles</span>
            <span style={{ color: systemStatus === 'healthy' ? '#00FF88' : '#F5A623' }}>
              {systemStatus === 'healthy' ? '● Datos reales' : '● Demo'}
            </span>
          </Space>
        </motion.div>
      </div>
    </div>
  );
};

const LandingPage = () => (
  <App>
    <LandingPageContent />
  </App>
);

export default LandingPage;
