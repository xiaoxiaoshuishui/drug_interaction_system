import request from '../utils/request';

const userService = {
  async login(userData) {
    try {
      const response = await request.post(`/api/user/login`, {
        username: userData.username,
        password: userData.password
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  async register(userData) {
    try {
      const response = await request.post(`/api/user/register`, {
        username: userData.username,
        password: userData.password
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  async getUserInfo(token) {
    try {
      const response = await request.get(`/api/user/info`, {
        headers: {
          Authorization: token
        }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  async updateUserBio(token, bio) {
    try {
      const response = await request.put(`/api/user/update`,
        { bio },
        {
          headers: {
            Authorization: token
          }
        }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  async updatePassword(token, oldPassword, newPassword) {
    try {
      const response = await request.put(`/api/user/password`,
        { oldPassword, newPassword },
        {
          headers: {
            Authorization: token
          }
        }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  async deleteAccount(){
  return request.delete('/api/user/account');
}
};

export default userService;