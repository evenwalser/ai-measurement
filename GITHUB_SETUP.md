# GitHub Repository Setup Guide

Follow these steps to create a GitHub repository and commit all the code we've developed for the Body Measurement API.

## Step 1: Create a New GitHub Repository

1. Go to [GitHub](https://github.com) and sign in to your account
2. Click the "+" icon in the top-right corner, then select "New repository"
3. Repository name: `body-measurement-api`
4. Description: "API for extracting accurate body measurements from images with multiple calibration methods, including LiDAR"
5. Choose "Public" or "Private" depending on your preference
6. Do NOT initialize with a README, .gitignore, or license (we'll add these from our local files)
7. Click "Create repository"

## Step 2: Initialize Your Local Repository

Open a terminal in the root directory of your project and run:

```bash
# Initialize a new git repository
git init

# Add your files to staging
git add .

# Create the initial commit
git commit -m "Initial commit: Body Measurement API with multiple calibration methods"
```

## Step 3: Connect and Push to GitHub

After creating the repository on GitHub, you'll see instructions on the page. Follow these to connect your local repository:

```bash
# Add the GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/body-measurement-api.git

# Push your changes to GitHub
git push -u origin main
```

If you're using the `master` branch instead:

```bash
git push -u origin master
```

## Step 4: Verify Your Repository Structure

After pushing, go to GitHub and check that all files are present. The repository should have the following structure:

```
body-measurement-api/
├── api/                        # API Layer (Laravel/PHP)
├── python/                     # Measurement Core
│   ├── spatiallm_bridge.py     # Bridge to SpatialLM
│   ├── spatiallm_repo/         # SpatialLM repository
│   └── wrapper.py              # Python measurement wrapper
├── testing-frontend/           # Testing Interface
│   ├── index.html              # Main testing interface
│   ├── lidar-capture.js        # LiDAR capture module
│   └── script.js               # Frontend scripts
├── test-images/                # Test images for development
├── DEVELOPMENT_PLAN.md         # Detailed development plan
├── README.md                   # Project documentation
├── docker-compose.yml          # Docker configuration
├── test-calibration.sh         # Automated testing script
├── start-testing.sh            # Environment setup script
├── test-spatiallm-integration.py # SpatialLM test script
└── .gitignore                  # Git ignore file
```

## Step 5: Create Meaningful Branches for Features (Optional)

If you'd like to organize your development work, consider creating branches for different features:

```bash
# Create and switch to a branch for spatial calibration
git checkout -b feature/spatial-calibration

# Create and switch to a branch for height-based calibration
git checkout -b feature/height-calibration

# Create and switch to a branch for reference object calibration
git checkout -b feature/reference-calibration
```

## Step 6: Update Repository Tags and Description (Optional)

On GitHub, add relevant tags to help people find your repository:
- body-measurement
- computer-vision
- lidar
- ios-integration
- api
- spatial-understanding
- ar
- php
- python
- machine-learning

## Step 7: Additional Repository Setup (Optional)

Consider adding these to your repository:
1. GitHub Actions workflow for automated testing
2. Issue templates for bug reports and feature requests
3. Pull request template
4. CONTRIBUTING.md file with guidelines

## Next Steps

1. Set up deployment to a staging or production environment
2. Add automated testing with GitHub Actions
3. Implement a versioning strategy for your API
4. Document the API with OpenAPI/Swagger
5. Consider setting up project boards for feature tracking

## Troubleshooting

### File Size Issues
If you encounter issues pushing large files, consider using Git LFS (Large File Storage):

```bash
# Install Git LFS
git lfs install

# Track large files (like test images, models)
git lfs track "*.jpg" "*.png" "*.pt"

# Add the .gitattributes file
git add .gitattributes

# Commit and push again
git commit -m "Set up Git LFS for large files"
git push
```

### Authentication Issues
If you have two-factor authentication enabled, you'll need to use a personal access token instead of your password when pushing to GitHub.

### Permission Denied
If you get "Permission denied" errors, make sure:
1. You have the correct repository URL
2. You have the necessary permissions for the repository
3. Your SSH keys or credentials are properly set up 