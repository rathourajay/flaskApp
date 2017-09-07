package cloud.edgenet.androidclient;

/*
    ENS Android Client
*/

import android.content.Context;
import android.util.Log;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.StringReader;
import java.io.UnsupportedEncodingException;
import java.net.InetAddress;
import java.net.Socket;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

import org.json.JSONException;
import org.json.JSONTokener;
import org.json.JSONObject;


public class ENSSession implements Runnable {

    public static final String TAG = "ENSSession";

    public enum SessionState { DISCONNECTED, CONNECTING, CONNECTED };

    public static final int MSG_EVENT = 0;
    public static final int MSG_HANDSHAKE = 1;

    private final ENSClient client;
    private final String ifName;
    private final String ifBinding;
    private final String token;
    private final ExecutorService executor;

    private final ENSSessionHandler handler;
    private SessionState state;

    private String cloudlet;
    private int probed_rtt;
    private InetAddress ipaddr;
    private int port;

    private Socket socket;
    private DataOutputStream out;
    private DataInputStream in;

    public ENSSession(ENSClient client, String cloudlet, String ifName, String ifBinding, String token, ExecutorService executor, ENSSessionHandler handler) {
        this.client = client;
        this.cloudlet = cloudlet;
        this.ifName = ifName;
        this.ifBinding = ifBinding;
        this.token = token;
        this.executor = executor;
        this.handler = handler;
        state = SessionState.DISCONNECTED;

        try {
            String[] binding = ifBinding.split(":");
            this.ipaddr = InetAddress.getByName(binding[0]);
            this.port = Integer.parseInt(binding[1]);
        }
        catch (Exception e)
        {
            Log.e(TAG, "Invalid binding for interface " + ifName + ": " + ifBinding);
            throw new IllegalStateException("Invalid binding for interface");
        }
    }

    public void connect() {
        /* Start the main processing loop */
        state = SessionState.CONNECTING;
        executor.submit(this);
    }

    public void close() {
        if (state == SessionState.CONNECTED) {
            try {
                this.socket.close();
            } catch (IOException e) {
            }
        }
        state = SessionState.DISCONNECTED;
    }

    public String cloudlet() {
        return this.cloudlet;
    }


    public void request(JSONObject req, Context context) {
        if (state != SessionState.CONNECTED) {
            throw new IllegalStateException("ENSSession not connected");
        }

        Log.d(TAG, "Sending request");
        try {
            /* Render the request to a string.  Use UTF-8 encoding for JSON */
            byte[] json = req.toString().getBytes("UTF-8");

            /* Lock the output stream and write the message */
            synchronized (this) {
                this.out.writeInt(json.length);
                this.out.writeInt(MSG_EVENT);
                this.out.write(json, 0, json.length);
                this.out.flush();
            }
        } catch (UnsupportedEncodingException e) {
            Log.e(TAG, "UnsupportedEncodingException: " + e.toString());
        } catch (IOException e) {
            Log.e(TAG, "IOException: " + e.toString());
        } catch (Exception e) {
            Log.e(TAG, "Unknown exception: " + e.toString());
        }

        Log.d(TAG, "Request completed");
    }

    @Override
    public void run() {

        /* Connect to the interface at the cloudlet and start exchanging data */
        try {
            Log.d(TAG, "Connecting to interface + " + this.ifName + " at " + this.ifBinding);
            this.socket = new Socket(this.ipaddr, this.port);
            Log.d(TAG, "Connected " + this.socket.isConnected());
            this.out = new DataOutputStream(new BufferedOutputStream(this.socket.getOutputStream()));
            this.in = new DataInputStream(new BufferedInputStream(this.socket.getInputStream()));

            /* Perform a handshake exchange to ensure the workload is loaded and connected */
            this.out.writeInt(0);
            this.out.writeInt(MSG_HANDSHAKE);
            this.out.flush();
            Log.d(TAG, "TX=>Sent handshake to " + this.ipaddr.toString());
            this.in.readInt();
            this.in.readInt();
            Log.d(TAG, "Received handshake response from " + this.ipaddr.toString());

            /* Call the handler to flag that the session is connected */
            state = SessionState.CONNECTED;
            Log.d(TAG, "Call onConnected()");
            handler.onConnected();
            Log.d(TAG, "onConnected() returned");

            try {
                /* Now loop processed received messages */
                while (state == SessionState.CONNECTED) {
                    Log.d(TAG, "Waiting for received message");
                    int len = this.in.readInt();
                    int id = this.in.readInt();
                    byte[] b = new byte[len];
                    this.in.readFully(b, 0, len);

                    switch (id) {
                    case MSG_EVENT:
                        String json = new String(b, "UTF-8");
                        try {
                            JSONObject rsp = (JSONObject)new JSONTokener(json).nextValue();
                            handler.onResponse(rsp);
                        } catch (JSONException e) {
                            Log.d(TAG, "JSON exception parsing received message");
                        }
                        break;

                    default:
                        break;
                    }
                }
            } catch (IOException e) {
                Log.d(TAG, "Session disconnected");
                state = SessionState.DISCONNECTED;
                handler.onDisconnected();
                return;
            }
        } catch (UnknownHostException e) {
            Log.e(TAG, "Unknown host exception connecting to interface " + this.ifName + " at " + this.ipaddr.toString() + ";" + Integer.toString(this.port));
            handler.onError();
            return;
        } catch (IOException e) {
            Log.e(TAG, "IO exception connecting to interface " + this.ifName + " at " + this.ipaddr.toString() + ";" + Integer.toString(this.port));
            handler.onError();
            return;
        } catch (Exception e) {
            Log.e(TAG, "Unknown exception: " + e.toString());
        }
    }

}


