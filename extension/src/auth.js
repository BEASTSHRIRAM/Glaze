// Authentication utilities for Glaze extension

export async function initiateAuth() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: 'initiateAuth' }, (response) => {
      resolve(response);
    });
  });
}

export async function getAccessToken() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: 'getAccessToken' }, (response) => {
      resolve(response);
    });
  });
}

export async function logout() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: 'logout' }, (response) => {
      resolve(response);
    });
  });
}

export async function isAuthenticated() {
  const tokenData = await getAccessToken();
  return tokenData.authenticated === true;
}
