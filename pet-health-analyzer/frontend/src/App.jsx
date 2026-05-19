import { useState } from 'react';
import OnboardingScreen from './screens/OnboardingScreen';
import EditProfileScreen from './screens/EditProfileScreen';
import ReportScreen from './screens/ReportScreen';
import './styles/global.css';

const SCREENS = {
  ONBOARDING: 'onboarding',
  REPORT: 'report',
  EDIT: 'edit',
};

function getInitialScreen() {
  try {
    const raw = localStorage.getItem('petProfile');
    if (raw) {
      const profile = JSON.parse(raw);
      if (profile.name) return SCREENS.REPORT;
    }
  } catch {
    // ignore
  }
  return SCREENS.ONBOARDING;
}

export default function App() {
  const [screen, setScreen] = useState(getInitialScreen);

  return (
    <div className="app-wrapper">
      {screen === SCREENS.ONBOARDING && (
        <OnboardingScreen onComplete={() => setScreen(SCREENS.REPORT)} />
      )}
      {screen === SCREENS.REPORT && (
        <ReportScreen onEdit={() => setScreen(SCREENS.EDIT)} />
      )}
      {screen === SCREENS.EDIT && (
        <EditProfileScreen
          onBack={() => setScreen(SCREENS.REPORT)}
          onReset={() => setScreen(SCREENS.ONBOARDING)}
        />
      )}
    </div>
  );
}
