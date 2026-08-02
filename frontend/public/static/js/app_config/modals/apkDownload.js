class ApkDownloadModal {
    constructor() {
        this._element = document.createElement('div');
        this._element.classList.add('modal', 'fade');
        this._element.setAttribute('tabindex', '-1');
        this._element.innerHTML = this._getHtml();
        this._root = this._element.querySelector('.modal-body');
        this.modal = new bootstrap.Modal(this._element);
        
        // Configurar eventos dos botões de download
        this._root.querySelectorAll('.__apk-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const version = btn.dataset.version;
                this._downloadApk(version);
            });
        });
    }

    _getHtml() {
        return `
        <div class="modal-dialog modal-md">
            <div class="modal-content">
                <div class="modal-header">
                    <h1 class="modal-title fs-5">BAIXAR APK</h1>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-2">
                    <div class="d-flex flex-column gap-2 justify-content-center">
                        <div class="card">
                            <div class="card-body p-2">
                                <h5 class="card-title d-flex justify-content-center">TUTORIAL</h5>
                                <p class="card-text">Assista esse vídeo para aprender como colocar suas credenciais no aplicativo.</p>
                                <a href="#" class="btn btn-dark w-100 mt-2">Alterar as credenciais</a>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-body p-2">
                                <h5 class="card-title d-flex justify-content-center">DTUNNEL SSH</h5>
                                <p class="card-text">Esta versão contém apenas o modo de conexão SSH</p>
                                <a href="#" class="btn btn-dark w-100 mt-2 __apk-btn" data-version="ssh">BAIXAR</a>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-body p-2">
                                <h5 class="card-title d-flex justify-content-center">DTUNNEL PRO</h5>
                                <p class="card-text">Esta versão contém apenas os modos de conexão SSH e OpenVPN</p>
                                <a href="#" class="btn btn-dark w-100 mt-2 __apk-btn" data-version="pro">BAIXAR</a>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-body p-2">
                                <h5 class="card-title d-flex justify-content-center">DTUNNEL V2RAY</h5>
                                <p class="card-text">Esta versão contém apenas modos de conexão SSH, OpenVPN e V2RAY</p>
                                <a href="#" class="btn btn-dark w-100 mt-2 __apk-btn" data-version="v2ray">BAIXAR</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
    }

    async _downloadApk(version) {
        try {
            showToastInfo('Preparando download do APK...');
            const response = await fetch(`/apk/download/${version}`);
            
            if (!response.ok) {
                const result = await response.json().catch(() => ({}));
                showToastError(result.message || 'APK não disponível no servidor');
                return;
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `dtunnel-${version}.apk`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showToastSuccess('Download iniciado com sucesso!');
            this.modal.hide();
        } catch (err) {
            showToastError('Erro ao baixar APK. Verifique se o arquivo está no servidor.');
        }
    }

    show() {
        this.modal.show();
    }

    hide() {
        this.modal.hide();
    }
}

export default ApkDownloadModal;
