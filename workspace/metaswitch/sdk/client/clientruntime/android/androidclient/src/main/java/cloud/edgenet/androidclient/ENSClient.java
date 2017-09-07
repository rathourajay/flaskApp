package cloud.edgenet.androidclient;

/*
    ENS Android Client
*/

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.InetAddress;
import java.net.Socket;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
/*
import android.content.Context;
import android.content.pm.PackageManager;
import android.content.pm.ApplicationInfo;
import android.net.ConnectivityManager;
import android.os.Bundle;
*/
import android.util.Log;
import org.json.JSONException;
import org.json.JSONTokener;
import org.json.JSONObject;
import org.json.JSONArray;

public class ENSClient {

    public static final String TAG = "ENSClient";

    public enum ClientState { INITIALIZING, INITIALIZED, FAILED };

    private final String application;
    private final ENSClientHandler handler;
    private ClientState clientState;
    private String ENSDomain;
    private String token;
    private String cloudlet;
    private Map<String, String> ifBindings;
    private ExecutorService executor;

    public static final int ENS_PROBE_PORT = 0xED01;
    public static final int ENS_PAAC_PORT  = 0xED02;

    /**
     * Creates a new ENSClient with default constructor arguments values
     */
    public ENSClient(String application, ENSClientHandler clientHandler) {
        this.application = application;
        this.handler = clientHandler;
        this.clientState = ClientState.INITIALIZING;

        /*
        try {
            ApplicationInfo ai = getPackageManager().getApplicationInfo(activity.getPackageName(), PackageManager.GET_META_DATA);
            Bundle bundle = ai.metaData;
            ENSDomain = bundle.getString("ENSDomain");
        } catch (NameNotFoundException e) {
            Log.e(LOG_TAG, "Failed to load meta-data, NameNotFound: " + e.getMessage());
        } catch (NullPointerException e) {
	          Log.e(LOG_TAG, "Failed to load meta-data, NullPointer: " + e.getMessage());			
        }
        */
        ENSDomain = "ens.edgenet.cloud";

        executor = Executors.newCachedThreadPool();

        InitCallback cb = new InitCallback() {
            public void onSuccess(String init_token, String init_cloudlet, Map<String, String> init_ifBindings) {
                token = init_token;
                cloudlet = init_cloudlet;
                ifBindings = init_ifBindings;
                clientState = ClientState.INITIALIZED;
                handler.onInitSuccess();
            }

            public void onFailure() {
                clientState = ClientState.FAILED;
                handler.onInitFailure();
            }
        };

        InitRequest init = new InitRequest(application, cb);
        executor.submit(init);
    }

    public ENSSession connect(String ifName, ENSSessionHandler handler) {
        if (clientState == ClientState.INITIALIZING) {
            throw new IllegalStateException("ENSClient still initializing");
        } else if (clientState == ClientState.FAILED) {
            throw new IllegalStateException("ENSClient failed to initialize");
        }

        String ifBinding = this.ifBindings.get(ifName);
        if (ifBinding == null) {
            throw new IllegalArgumentException("Unknown interface " + ifName);
        }

        ENSSession session = new ENSSession(this, this.cloudlet, ifName, ifBinding, this.token, executor, handler);
        session.connect();
        return session;
    }

    private interface InitCallback {
        void onSuccess(String init_token, String init_cloudlet, Map<String, String> init_ifBindings);
        void onFailure();
    }

    private class InitRequest implements Runnable {

        private final String application;
        private final InitCallback init_cb;

        public InitRequest(String application, InitCallback cb) {
            this.application = application;
            this.init_cb = cb;
        }

        @Override
        public void run() {
            /* Check network connectivity
             */
            /*
            ConnectivityManager connMgr = (ConnectivityManager)getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkInfo networkInfo = connMgr.getActiveNetworkInfo();
            if ((networkInfo == null) || (networkInfo.isConnected())) {
                cb.onFailure();
                return;
            }
            */

            Log.i(TAG, "Starting initialization for " + application);

            List<String> cloudlets = new ArrayList<String>();

            InetAddress[] paac = new InetAddress[0];
            try {
                paac = InetAddress.getAllByName(ENSDomain);
            } catch (UnknownHostException e) {
                Log.e(TAG, "Failed to resolve ENS domain name " + ENSDomain + " : " + e.toString());
            }

            for (int ii = 0; ii < paac.length; ii++) {
                try {
                    Log.d(TAG, "Attempt to get cloudlet shortlist from " + paac[ii].toString());
                    Socket s = new Socket(paac[ii], ENS_PAAC_PORT);
                    Log.d(TAG, "Connected " + s.isConnected());

                    BufferedWriter out = new BufferedWriter(new OutputStreamWriter(s.getOutputStream()));
                    BufferedReader in = new BufferedReader(new InputStreamReader(s.getInputStream()));

                    String inquire_req = String.format("ENS-INQUIRE %s\r\n", application);
                    out.write(inquire_req, 0, inquire_req.length());
                    out.flush();
                    Log.d(TAG, "TX=>" + paac[ii].toString() + ": " + inquire_req.replace("\r",""));

                    String inquire_rsp = in.readLine();
                    Log.d(TAG, "RX<=" + paac[ii].toString() + ": " + inquire_rsp.replace("\r",""));
                    String[] params = inquire_rsp.split(" ");

                    if (params[0].equals("ENS-INQUIRE-OK")) {
                        String json = in.readLine();
                        Log.i(TAG, "Retrieved cloudlet shortlist successfully: " + json);
                        JSONObject inquire_data = (JSONObject) new JSONTokener(json).nextValue();
                        JSONArray c = inquire_data.getJSONArray("cloudlets");
                        for (int jj = 0; jj < c.length(); jj++) {
                            cloudlets.add(c.getString(jj));
                        }
                    }
                    s.close();
                    break;
                } catch (JSONException e) {
                    Log.e(TAG, "Exception parsing ENS-INQUIRE-OK response from " + paac[ii].toString() + " : " + e.toString());
                } catch (UnknownHostException e) {
                    Log.w(TAG, "Failed to connected to ENS platform app@cloud " + paac[ii].toString() + " : " + e.toString());
                } catch (IOException e) {
                    Log.w(TAG, "IO exception during application initialization: " + e.toString());
                }
            }

            if (cloudlets.size() == 0)
            {
                Log.e(TAG, "No candidate cloudlets for service");
                init_cb.onFailure();
                return;
            }

            final CountDownLatch cdl = new CountDownLatch(cloudlets.size());
            List<Probe> probes = new ArrayList<Probe>();

            ProbeCallback probe_cb = new ProbeCallback() {
                public void onComplete() {
                    cdl.countDown();
                }
            };

            for (String c : cloudlets) {
                Log.d(TAG, "Create probe for " + c);
                Probe probe = new Probe(c, probe_cb);
                probes.add(probe);
                executor.submit(probe);
            }

            /* Wait for all probes to complete or timeout */
            try {
                Log.d(TAG, "Wait for probes to complete");
                cdl.await(1L, TimeUnit.SECONDS);
                Log.d(TAG, "Probes completed");
            } catch (InterruptedException e) {
                Log.w(TAG, "Exception waiting for probes to complete");
            }

            /* Sort the probes on RTT */
            Collections.sort(probes);

            /* Get the lowest RTT entry */
            Probe p = probes.get(0);

            if (p.rtt() == 0) {
                Log.e(TAG, "All probes failed");
                init_cb.onFailure();
                return;
            }

            String cloudlet = p.cloudlet();
            int probed_rtt = p.rtt();
            Log.i(TAG, "Instantiating application " + application + " on cloudlet " + cloudlet);

            Map<String, String> ifBindingMap = new HashMap<String, String>();

            /* Connect to PAAC to instantiate the application */
            for (int ii = 0; ii < paac.length; ii++) {
                try {
                Socket s = new Socket(paac[ii], ENSClient.ENS_PAAC_PORT);
                    Log.d(TAG, "Connected " + s.isConnected());

                    BufferedWriter out = new BufferedWriter(new OutputStreamWriter(s.getOutputStream()));
                    BufferedReader in = new BufferedReader(new InputStreamReader(s.getInputStream()));

                    String service_req = String.format("ENS-SERVICE %s %s %s\r\n", application, cloudlet, probed_rtt);
                    out.write(service_req, 0, service_req.length());
                    out.flush();
                    Log.d(TAG, "TX=>" + paac[ii].toString() + ": " + service_req.replace("\r",""));

                    String service_rsp = in.readLine();
                    Log.d(TAG, "RX<=" + paac[ii].toString() + ": " + service_rsp.replace("\r",""));
                    String[] params = service_rsp.split(" ");

                    if (!params[0].equals("ENS-SERVICE-OK")) {
                        Log.e(TAG, "Failed to instantiate application " + application);
                        init_cb.onFailure();
                        return;
                    }

                    String json = in.readLine();
                    Log.d(TAG, "Application metadata: " + json);
                    JSONObject bindings = (JSONObject)new JSONTokener(json).nextValue();

                    Iterator<String> iterator = bindings.keys();
                    while (iterator.hasNext()) {
                        String ifName = iterator.next();
                        String ifBinding = bindings.getString(ifName);
                        ifBindingMap.put(ifName, ifBinding);
                    }

                    s.close();
                    break;

                } catch (JSONException e) {
                    Log.e(TAG, "JSON exception during application instantiation");
                    init_cb.onFailure();
                    return;
                } catch (UnknownHostException e) {
                    Log.e(TAG, "Unknown host exception during application instantiation");
                    init_cb.onFailure();
                    return;
                } catch (IOException e) {
                    Log.e(TAG, "IO exception during application instantiation");
                    init_cb.onFailure();
                    return;
                }
            }

            init_cb.onSuccess("", cloudlet, ifBindingMap);
        }
    }

    private interface ProbeCallback {
        void onComplete();
    }

    private class Probe implements Runnable, Comparable<Probe> {

        private final String cloudlet;
        private final ProbeCallback cb;
        private List<Integer> samples = Collections.synchronizedList(new ArrayList<Integer>());
        private InetAddress ia;
        boolean cancelled = false;

        public Probe(String cloudlet, ProbeCallback cb) {
            this.cloudlet = cloudlet;
            this.cb = cb;
        }

        @Override
        public void run() {
            try {
                ia = InetAddress.getByName(cloudlet);
                Log.d(TAG, "Starting probe to " + ia.toString());

                Socket s = new Socket(ia, ENSClient.ENS_PROBE_PORT);
                Log.d(TAG, "Probe " + ia.toString() + " connected " + s.isConnected());

                BufferedWriter out = new BufferedWriter(new OutputStreamWriter(s.getOutputStream()));
                BufferedReader in = new BufferedReader(new InputStreamReader(s.getInputStream()));

                String probe = String.format("ENS-PROBE %s\r\n", application);
                out.write(probe, 0, probe.length());
                out.flush();
                Log.d(TAG, "TX: " + probe.replace("\r",""));
                String probe_rsp = in.readLine();
                Log.d(TAG, "RX: " + probe_rsp.replace("\r",""));
                String[] params = probe_rsp.split(" ");

                if (params[0].equals("ENS-PROBE-OK")) {
                    /* Microservice is supported, so start RTT probing */
                    Log.d(TAG, "Probe to " + ia.toString() + " accepted");
                    String rtt = String.format("ENS-RTT %s\r\n", application);
                    for (int ii = 0; ii < 10; ++ii) {
                        if (cancelled) {
                            break;
                        }
                        out.write(rtt, 0, rtt.length());
                        Log.d(TAG, "TX: " + rtt.replace("\r",""));
                        long start = System.nanoTime();
                        out.flush();
                        String rtt_rsp = in.readLine();
                        long stop = System.nanoTime();
                        Log.d(TAG, "RX: " + rtt_rsp.replace("\r",""));
                        Log.d(TAG, ia.toString() + " probe RTT sample " + (int)(stop - start) + "ns");
                        samples.add((int)(stop - start));
                    }
                } else {
                    Log.e(TAG, "Probe to " + ia.toString() + " rejected: " + params[0]);
                }
                Log.d(TAG, "Probe to " + ia.toString() + " completed, RTT = " + Integer.toString(rtt()) + "ns");

            }
            catch (UnknownHostException e) {
                Log.e(TAG, "Unknown host exception probing cloudlet " + cloudlet);
            }
            catch (IOException e) {
                Log.e(TAG, "IO exception probing cloudlet " + cloudlet);
            }

            cb.onComplete();
        }

        public int rtt() {
            Integer sum = 0;
            Integer count = 0;
            synchronized(samples) {
                for (Integer ii : samples) {
                    sum += ii;
                    count++;
                }
            }
            if (count > 0) {
                return sum/count;
            } else {
                return Integer.MAX_VALUE;
            }
        }

        public String cloudlet() {
            return cloudlet;
        }

        public InetAddress ipaddr() {
            return ia;
        }

        @Override
        public int compareTo(Probe o) {
            return rtt() - o.rtt();
        }
    }
}



