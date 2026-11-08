// Next.js accepts --hostname, while some preview launchers send Vite-style flags.
import {spawn} from 'node:child_process';
const args=process.argv.slice(2).filter(x=>x!=='--strictPort').map(x=>x==='--host'?'--hostname':x);
const child=spawn(process.execPath,['node_modules/next/dist/bin/next','dev',...args],{stdio:'inherit'});
for(const s of ['SIGINT','SIGTERM'])process.on(s,()=>child.kill(s));
child.on('exit',code=>process.exit(code??1));
