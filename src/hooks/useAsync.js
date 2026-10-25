import { useCallback, useEffect, useState } from 'react';
export default function useAsync(fn, deps = [], intervalSec = 0) {
  const [s, setS] = useState({ data: null, error: null, loading: true });
  const run = useCallback((silent) => {
    if (!silent) setS((p) => ({ ...p, loading: true, error: null }));
    return fn().then((data) => setS({ data, error: null, loading: false }), (error) => setS({ data: null, error, loading: false }));
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { run(); }, [run]);
  useEffect(() => { if (!intervalSec) return; const id = setInterval(() => run(true), intervalSec * 1000); return () => clearInterval(id); }, [intervalSec, run]);
  return { ...s, reload: () => run(false) };
}
