package cloud.edgenet.latencycheck;

import android.os.Bundle;
import android.os.Handler;
import android.support.design.widget.FloatingActionButton;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.util.Log;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import cloud.edgenet.androidclient.ENSClient;
import cloud.edgenet.androidclient.ENSSession;
import cloud.edgenet.androidclient.ENSClientHandler;
import cloud.edgenet.androidclient.ENSSessionHandler;

public class MainActivity extends AppCompatActivity {

    private Handler updateTextHandler;

    private TextView textView;
    private ScrollView scrollView;

    private LatencyTester tester = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        updateTextHandler = new Handler();
        textView = (TextView)findViewById(R.id.text);
        scrollView = (ScrollView)findViewById(R.id.scroll);

        FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
        fab.setImageResource(R.drawable.ic_play_arrow_black_24dp);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
                if (tester == null) {
                    textView.setText("");
                    tester = new LatencyTester();
                    fab.setImageResource(R.drawable.ic_pause_black_24dp);
                } else {
                    tester.close();
                    tester = null;
                    fab.setImageResource(R.drawable.ic_play_arrow_black_24dp);
                }
            }
        });

    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    private class AppendText implements Runnable {
        private String output;

        public AppendText(String output) {
            this.output = output;
        }

        @Override
        public void run() {
            // textView.setText(textView.getText().toString()+this.output+"\n");
            textView.append(this.output+"\n");
            scrollView.post(new Runnable() {
                public void run() {
                    scrollView.scrollTo(0, textView.getMeasuredHeight());
                }
            });
        }
    }

    private class LatencyTester implements Runnable, ENSClientHandler, ENSSessionHandler {

        private ENSClient ensClient = null;
        private ENSSession ensSession = null;
        private int iteration = 0;
        private long startTime = -1L;
        private List<Integer> samples = Collections.synchronizedList(new ArrayList<Integer>());
        private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
        private boolean running = true;

        LatencyTester() {
            scheduler.execute(this);
        }

        public void close() {
            running = false;
        }

        @Override
        public void run() {
            if (ensClient == null) {
                if (running) {
                    ensClient = new ENSClient("ens.latency-test", this);
                    updateTextHandler.post(new AppendText("Connecting"));
                    iteration = 0;
                    samples.clear();
                }
            } else {
                iteration += 1;
                try {
                    JSONObject req = (JSONObject) new JSONTokener("{\"Iteration\": " + Integer.toString(iteration) + "}").nextValue();
                    startTime = System.nanoTime();
                    ensSession.request(req, null);
                } catch (JSONException e) {
                } catch (IllegalStateException e) {
                }
            }
        }

        @Override
        public void onInitSuccess() {
            ensSession = ensClient.connect("latencyresponder.ping", this);
        }

        @Override
        public void onInitFailure() {
            updateTextHandler.post(new AppendText("Failed to initialize application"));
            ensClient = null;
            report("auth-error");
            scheduler.schedule(this, 5L, TimeUnit.SECONDS);
        }

        @Override
        public void onConnected() {
            updateTextHandler.post(new AppendText("Connected to " + ensSession.cloudlet()));
            scheduler.execute(this);
        }

        @Override
        public void onResponse(JSONObject rsp) {
            long endTime = System.nanoTime();
            int latency = (int)(endTime - startTime);
            samples.add(latency);

            if (samples.size() == 10) {
                double mean_latency = (double)mean_latency()/1000000000.0;
                updateTextHandler.post(new AppendText("Latency = " + Double.toString(mean_latency)));
                report("active", ensSession.cloudlet(), mean_latency);
                ensSession.close();
                ensSession = null;
                ensClient = null;
                scheduler.schedule(this, 5L, TimeUnit.SECONDS);
            } else {
                scheduler.schedule(this, 100L, TimeUnit.MILLISECONDS);
            }
        }

        @Override
        public void onDisconnected() {
        }

        @Override
        public void onError() {
            updateTextHandler.post(new AppendText("Failed to connect to application"));
            report("sess-error");
            scheduler.schedule(this, 5L, TimeUnit.SECONDS);
        }

        private void report(String status) {
            JSONObject json = new JSONObject();
            try {
                json.put("status", status);
                report(json);
            } catch (JSONException e) {
            }
        }

        private void report(String status, String cloudlet, double latency) {
            JSONObject json = new JSONObject();
            try {
                json.put("status", status);
                json.put("cloudlet", cloudlet);
                json.put("latency", latency);
                report(json);
            } catch (JSONException e) {
            }
        }

        private void report(JSONObject json) {

            try {
                URL url = new URL("http://dashboard.edgenet.cloud/sample");
                HttpURLConnection urlConnection = (HttpURLConnection) url.openConnection();
                urlConnection.setDoOutput(true);
                urlConnection.setRequestMethod("POST");
                urlConnection.setUseCaches(false);
                urlConnection.setConnectTimeout(10000);
                urlConnection.setReadTimeout(10000);
                urlConnection.setRequestProperty("Accept", "application/json");
                urlConnection.setRequestProperty("Content-Type","application/json");
                urlConnection.connect();
                OutputStreamWriter out = new OutputStreamWriter(urlConnection.getOutputStream());
                out.write(json.toString());
                out.close();

                int HttpResult = urlConnection.getResponseCode();
                if (HttpResult != HttpURLConnection.HTTP_OK) {
                    updateTextHandler.post(new AppendText("Failed to send report, HTTP status = " + HttpResult));
                }

            } catch (Exception e) {
                updateTextHandler.post(new AppendText("Exception sending report: " + e.toString()));
            }
        }

        private int mean_latency() {
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
                return 0;
            }
        }

    }
}
