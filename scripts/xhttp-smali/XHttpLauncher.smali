.class public final Lcom/dtunnel/xhttp/XHttpLauncher;
.super Ljava/lang/Object;
.source "XHttpLauncher.smali"


.method private constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


.method public static start(Landroid/content/Context;Lg4/e;)V
    .locals 10

    # Persist the profile fields consumed by the embedded GPLv3 XHTTP service.
    const-string v0, "xhttp_demo_private"

    const/4 v1, 0x0

    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    # XHTTP endpoint and port come from the standard server object.
    iget-object v1, p1, Lg4/e;->r:Lg4/d;

    iget-object v1, v1, Lg4/d;->l:Ljava/lang/String;

    const-string v2, "sshServer"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    iget-object v1, p1, Lg4/e;->r:Lg4/d;

    iget v1, v1, Lg4/d;->m:I

    invoke-static {v1}, Ljava/lang/Integer;->toString(I)Ljava/lang/String;

    move-result-object v1

    const-string v2, "sshPort"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    # SSH credentials are already part of every panel configuration.
    iget-object v1, p1, Lg4/e;->p:Lg4/a;

    iget-object v1, v1, Lg4/a;->l:Ljava/lang/String;

    const-string v2, "sshUser"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    # config_payload.sni is represented by the first payload field in the base APK.
    iget-object v1, p1, Lg4/e;->m:Lg4/b;

    if-eqz v1, :cond_sni_empty

    iget-object v1, v1, Lg4/b;->l:Ljava/lang/String;

    if-nez v1, :cond_sni_ready

    :cond_sni_empty
    const-string v1, ""

    :cond_sni_ready
    const-string v2, "xhttpSni"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    # config_payload.payload is dedicated to the XHTTP request path in this mode.
    iget-object v1, p1, Lg4/e;->m:Lg4/b;

    if-eqz v1, :cond_path_default

    iget-object v1, v1, Lg4/b;->m:Ljava/lang/String;

    if-nez v1, :cond_path_ready

    :cond_path_default
    const-string v1, "/ssh"

    :cond_path_ready
    const-string v2, "xhttpPath"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    # proxy.host is the HTTP Host header (proxy.port is intentionally unused for XHTTP).
    iget-object v1, p1, Lg4/e;->q:Lg4/d;

    iget-object v1, v1, Lg4/d;->l:Ljava/lang/String;

    if-nez v1, :cond_host_ready

    const-string v1, ""

    :cond_host_ready
    const-string v2, "xhttpHost"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    # The XHTTP-only value NONE disables TLS. Any normal TLS version enables it.
    const-string v1, "NONE"

    iget-object v2, p1, Lg4/e;->E:Ljava/lang/String;

    invoke-virtual {v1, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-eqz v3, :cond_tls_enabled

    const-string v3, "0"

    goto :goto_tls_value

    :cond_tls_enabled
    const-string v3, "1"

    :goto_tls_value
    const-string v4, "xhttpTls"

    invoke-interface {v0, v4, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v3, "TLSv1.2"

    invoke-virtual {v3, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_tls13

    const-string v2, "1"

    goto :goto_tls12_value

    :cond_tls13
    const-string v2, "0"

    :goto_tls12_value
    const-string v3, "tls12"

    invoke-interface {v0, v3, v2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v2, "localSocksPort"

    const-string v3, "1080"

    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    # Keep DNS and UDP defaults aligned with the profile when they are supplied.
    const-string v0, "xhttp_demo_vpn"

    const/4 v1, 0x0

    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "dnsForward"

    const/4 v2, 0x1

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    iget-object v1, p1, Lg4/e;->B:Lg4/c;

    iget-object v1, v1, Lg4/c;->l:Ljava/lang/String;

    if-nez v1, :cond_dns1_ready

    const-string v1, "1.1.1.1"

    :cond_dns1_ready
    const-string v2, "dnsResolver"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    iget-object v1, p1, Lg4/e;->B:Lg4/c;

    iget-object v1, v1, Lg4/c;->m:Ljava/lang/String;

    if-nez v1, :cond_dns2_ready

    const-string v1, "1.0.0.1"

    :cond_dns2_ready
    const-string v2, "dnsResolverSecondary"

    invoke-interface {v0, v2, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "udpForward"

    const/4 v2, 0x1

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "udpResolver"

    const-string v2, "127.0.0.1:7300"

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "disableIpv6Tunnel"

    const/4 v2, 0x1

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    # The password is deliberately passed only as a service extra, not written to disk.
    new-instance v0, Landroid/content/Intent;

    const-class v1, Lcom/dragonssh/xhttpdemo/core/XHttpSshService;

    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v1, "ssh_password"

    iget-object v2, p1, Lg4/e;->p:Lg4/a;

    iget-object v2, v2, Lg4/a;->m:Ljava/lang/String;

    if-nez v2, :cond_password_ready

    const-string v2, ""

    :cond_password_ready
    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    move-result-object v0

    invoke-static {p0, v0}, Lb0/b;->e(Landroid/content/Context;Landroid/content/Intent;)V

    return-void
.end method
