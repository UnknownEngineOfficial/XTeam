import React from 'react';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';
import Button from '../common/Button';

interface PreviewControlsProps {
  isPlaying: boolean;
  onPlay: () => void;
  onPause: () => void;
  onRestart: () => void;
  onSettings: () => void;
  className?: string;
}

const PreviewControls: React.FC<PreviewControlsProps> = ({
  isPlaying,
  onPlay,
  onPause,
  onRestart,
  onSettings,
  className = '',
}) => {
  return (
    <div className={`flex items-center justify-center space-x-2 p-3 bg-gray-50 border-b border-gray-200 ${className}`}>
      <Button
        variant="ghost"
        size="sm"
        onClick={isPlaying ? onPause : onPlay}
        className="p-2"
        title={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? (
          <Pause className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4" />
        )}
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={onRestart}
        className="p-2"
        title="Restart"
      >
        <RotateCcw className="w-4 h-4" />
      </Button>

      <div className="w-px h-6 bg-gray-300 mx-2" />

      <Button
        variant="ghost"
        size="sm"
        onClick={onSettings}
        className="p-2"
        title="Settings"
      >
        <Settings className="w-4 h-4" />
      </Button>
    </div>
  );
};

export default PreviewControls;
