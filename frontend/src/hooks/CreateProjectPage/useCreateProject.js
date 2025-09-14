import { checkProjectExistsAPI, createProjectAPI  } from "../../api/CreateProjectPage/api.js";

export default function useCreateProject() {
  const createProject = async (data) => {
    return createProjectAPI(data); // data = { title, token, ... }
  };

  const checkProjectExists = async (projectName) => {
    return checkProjectExistsAPI(projectName); 
  };

  return { createProject, checkProjectExists };
}