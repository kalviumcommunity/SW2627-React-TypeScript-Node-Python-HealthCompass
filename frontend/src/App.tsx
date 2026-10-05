import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import AskHealthCompass from './pages/AskHealthCompass';
import GuidanceLibrary from './pages/GuidanceLibrary';
import Updates from './pages/Updates';
import Alerts from './pages/Alerts';
import SavedGuidance from './pages/SavedGuidance';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="ask" element={<AskHealthCompass />} />
          <Route path="guidance" element={<GuidanceLibrary />} />
          <Route path="updates" element={<Updates />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="saved" element={<SavedGuidance />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
