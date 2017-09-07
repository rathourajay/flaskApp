package cloud.edgenet.androidclient;

import org.json.JSONObject;

/*
    ENS Android Client
*/

public interface ENSSessionHandler {
    void onConnected();
    void onResponse(JSONObject rsp);
    void onDisconnected();
    void onError();
}

