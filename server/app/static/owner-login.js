"use strict";
const {clientId,nonce}=document.body.dataset;
const status=document.getElementById("status");
function initialise(){
  if(!window.google?.accounts?.id){
    status.textContent="Google sign-in unavailable. Check your connection and reload.";
    return;
  }
  google.accounts.id.initialize({
    client_id:clientId,
    nonce,
    auto_select:false,
    callback:async ({credential})=>{
      if(!credential){status.textContent="Sign-in cancelled.";return;}
      status.textContent="Verifying your Google account…";
      try{
        const response=await fetch("/owner/session",{
          method:"POST",credentials:"same-origin",
          headers:{"Content-Type":"application/json","X-Owner-Login-Nonce":nonce},
          body:JSON.stringify({credential})
        });
        if(!response.ok)throw Error(response.status===403?"This account is not authorised for the dashboard.":"Sign-in verification failed.");
        window.location.assign("/owner/analytics");
      }catch(error){status.textContent=error.message;}
    }
  });
  google.accounts.id.renderButton(document.getElementById("google-button"),{
    theme:"outline",size:"large",text:"signin_with",shape:"pill",width:280
  });
  status.textContent="Choose your Google account to continue.";
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>setTimeout(initialise,300));
else setTimeout(initialise,300);
