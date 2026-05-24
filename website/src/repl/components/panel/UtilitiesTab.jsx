import cx from '@src/cx.mjs';
import { useState } from 'react';
import { Textbox } from '@src/repl/components/panel/SettingsTab';

function Checkbox({ label, value, onChange, disabled = false }) {
  return (
    <label className={cx('text-sm', disabled && 'opacity-50')}>
      <input disabled={disabled} type="checkbox" checked={value} onChange={onChange} />
      {' ' + label}
    </label>
  );
}

function FormItem({ label, children, disabled = false }) {
  return (
    <div className={cx('grid gap-2 w-full', disabled && 'opacity-50')}>
      <label className="text-sm">{label}</label>
      {children}
    </div>
  );
}

function ActionButton({ label, onClick, disabled = false }) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={cx(
        'bg-background p-2 rounded-md hover:opacity-75 border border-muted text-foreground text-sm',
        disabled && 'opacity-50',
      )}
    >
      {label}
    </button>
  );
}

export function UtilitiesTab({ context }) {
  const [downloadName, setDownloadName] = useState('atlas-render');
  const [startCycle, setStartCycle] = useState(0);
  const [endCycle, setEndCycle] = useState(8);
  const [sampleRate, setSampleRate] = useState(48000);
  const [width, setWidth] = useState(1600);
  const [height, setHeight] = useState(900);
  const [labels, setLabels] = useState(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('Ready. Evaluate code, then export WAV, pianoroll, or both.');

  const wavOptions = {
    begin: startCycle,
    end: endCycle,
    sampleRate,
    downloadName,
  };

  const pianorollOptions = {
    begin: startCycle,
    end: endCycle,
    width,
    height,
    labels: labels ? 1 : 0,
    downloadName: `${downloadName}-pianoroll`,
  };

  async function run(label, fn) {
    try {
      setBusy(true);
      setStatus(`${label}…`);
      const result = await fn();
      setStatus(`${label} complete${result?.fileName ? `: ${result.fileName}` : ''}`);
      return result;
    } catch (err) {
      console.error(err);
      setStatus(`${label} failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="text-foreground w-full space-y-4 p-4">
      <div className="text-sm text-muted-foreground">
        Mobile-friendly render utilities. These run on the current evaluated pattern, so you do not need the browser console.
      </div>

      <FormItem label="Base file name" disabled={busy}>
        <Textbox
          value={downloadName}
          onChange={setDownloadName}
          disabled={busy}
          placeholder="atlas-render"
          className={cx(busy && 'opacity-50 border-opacity-50')}
        />
      </FormItem>

      <div className="flex flex-row gap-4 w-full">
        <FormItem label="Start cycle" disabled={busy}>
          <Textbox
            type="number"
            value={startCycle}
            onChange={(v) => setStartCycle(parseInt(v || '0', 10) || 0)}
            disabled={busy}
            className={cx(busy && 'opacity-50 border-opacity-50', 'w-full')}
          />
        </FormItem>
        <FormItem label="End cycle" disabled={busy}>
          <Textbox
            type="number"
            value={endCycle}
            onChange={(v) => setEndCycle(Math.max(startCycle + 1, parseInt(v || '0', 10) || 1))}
            disabled={busy}
            className={cx(busy && 'opacity-50 border-opacity-50', 'w-full')}
          />
        </FormItem>
      </div>

      <div className="flex flex-row gap-4 w-full">
        <FormItem label="WAV sample rate" disabled={busy}>
          <Textbox
            type="number"
            value={sampleRate}
            onChange={(v) => setSampleRate(Math.max(8000, parseInt(v || '0', 10) || 48000))}
            disabled={busy}
            className={cx(busy && 'opacity-50 border-opacity-50', 'w-full')}
          />
        </FormItem>
        <FormItem label="Pianoroll width" disabled={busy}>
          <Textbox
            type="number"
            value={width}
            onChange={(v) => setWidth(Math.max(400, parseInt(v || '0', 10) || 1600))}
            disabled={busy}
            className={cx(busy && 'opacity-50 border-opacity-50', 'w-full')}
          />
        </FormItem>
      </div>

      <div className="flex flex-row gap-4 w-full">
        <FormItem label="Pianoroll height" disabled={busy}>
          <Textbox
            type="number"
            value={height}
            onChange={(v) => setHeight(Math.max(200, parseInt(v || '0', 10) || 900))}
            disabled={busy}
            className={cx(busy && 'opacity-50 border-opacity-50', 'w-full')}
          />
        </FormItem>
        <FormItem label="Pianoroll labels" disabled={busy}>
          <div className="h-8 flex items-center">
            <Checkbox label="Show labels" value={labels} onChange={(e) => setLabels(e.target.checked)} disabled={busy} />
          </div>
        </FormItem>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <ActionButton
          disabled={busy}
          label={busy ? 'Working…' : 'Export WAV'}
          onClick={() => run('WAV export', () => context.handleRenderWav(wavOptions))}
        />
        <ActionButton
          disabled={busy}
          label={busy ? 'Working…' : 'Export Pianoroll'}
          onClick={() => run('Pianoroll export', () => context.handleRenderPianoroll(pianorollOptions))}
        />
        <ActionButton
          disabled={busy}
          label={busy ? 'Working…' : 'Export Both'}
          onClick={() =>
            run('Bundle export', () =>
              context.handleRenderBundle({
                wav: wavOptions,
                pianoroll: pianorollOptions,
              }),
            )
          }
        />
      </div>

      <div className="text-xs text-muted-foreground border border-muted rounded-md p-3 break-words">{status}</div>
    </div>
  );
}
